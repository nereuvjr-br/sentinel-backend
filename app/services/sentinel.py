import asyncio
import paramiko
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.future import select
from app.core.config import settings
from app.core.database import get_session
from app.models.all_models import ServiceOffset
from app.services.parsers import LogParser

# Mapping global para as classes do parser, facilitando a injeção no BD
from app.models.all_models import (
    LogChat, LogKill, LogLogin, LogViolation, 
    LogAdmin, LogEconomy, LogVehicle, LogChest, 
    LogGameplay, LogFame
)

class SentinelDaemon:
    def __init__(self):
        self.host = settings.SFTP_HOST
        self.port = settings.SFTP_PORT
        self.username = settings.SFTP_USER
        self.password = settings.SFTP_PASS
        self.remote_path = os.getenv("REMOTE_LOG_PATH", "/138.199.5.114_7122/SaveFiles/Logs")
        
        self.ssh_client = None
        self.sftp = None
        
        self.offsets_cache: Dict[str, int] = {}

    async def connect(self):
        """Estabelece conexão SSH/SFTP persistente."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f"🔌 Tentando conectar em {self.host}:{self.port}...")
            
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            self.sftp = self.ssh_client.open_sftp()
            print("✅ Conectado ao SFTP com sucesso!")
        except Exception as e:
            print(f"🔥 Erro de conexão: {e}")
            raise

    async def sync_offsets_cache(self):
        """Carrega o estado atual dos offsets do banco para a memória."""
        async for session in get_session():
            # CORREÇÃO: Usar .execute() padrão do SQLAlchemy AsyncSession
            result = await session.execute(select(ServiceOffset))
            offsets = result.scalars().all()
            for record in offsets:
                self.offsets_cache[record.filename] = record.last_read_offset
            print(f"🧠 Cache sincronizado: {len(self.offsets_cache)} arquivos rastreados.")
            return

    async def run_forever(self):
        await self.sync_offsets_cache()
        
        while True:
            try:
                if not self.sftp:
                    await self.connect()
                
                await self.scan_and_process()
                
            except Exception as e:
                print(f"⚠️ Erro no loop principal: {e}")
                import traceback
                traceback.print_exc()
                
                # Força reconexão limpa
                if self.ssh_client: self.ssh_client.close()
                self.sftp = None
                self.ssh_client = None
                await asyncio.sleep(5)  # Backoff
            
            await asyncio.sleep(2)  # Polling interval

    async def scan_and_process(self):
        """Lista arquivos e processa os modificados."""
        try:
            files = self.sftp.listdir_attr(self.remote_path)
        except IOError:
            print(f"❌ Falha ao listar diretório {self.remote_path}.")
            return

        now = datetime.now().timestamp()
        retention_window = settings.LOG_RETENTION_HOURS * 3600
        
        active_files = []
        for f in files:
            if not f.filename.endswith(".log"): continue
            # Filtro 24h
            if (now - f.st_mtime) > retention_window:
                continue
            active_files.append(f)

        async for session in get_session():
            for f in active_files:
                cached_offset = self.offsets_cache.get(f.filename, 0)
                
                if f.st_size > cached_offset:
                    print(f"📜 Detectado update em {f.filename} (Novo: {f.st_size} bytes)")
                    await self.process_file_delta(session, f.filename, cached_offset, f.st_size)
    
    async def process_file_delta(self, session, filename, start_offset, end_offset):
        full_path = f"{self.remote_path}/{filename}"
        
        try:
            with self.sftp.open(full_path, 'r', bufsize=32768) as remote_file:
                remote_file.seek(start_offset)
                content_bytes = remote_file.read(end_offset - start_offset)
                
                try:
                    content_str = content_bytes.decode('utf-16-le', errors='replace')
                except Exception as decode_err:
                    print(f"💀 Erro decodificando {filename}: {decode_err}")
                    return

                new_cursor = end_offset 
                lines = content_str.splitlines()
                batch_models = []
                
                for line in lines:
                    parsed_obj = LogParser.process_line(filename, line)
                    if parsed_obj:
                        batch_models.append(parsed_obj)
                
                if batch_models:
                    session.add_all(batch_models)
                    await session.commit()
                    print(f"💾 {len(batch_models)} eventos salvos de {filename}")
                
                self.offsets_cache[filename] = new_cursor
                
                record = await session.get(ServiceOffset, filename)
                if not record:
                    record = ServiceOffset(filename=filename, last_read_offset=new_cursor)
                    session.add(record)
                else:
                    record.last_read_offset = new_cursor
                    record.updated_at = datetime.utcnow()
                    session.add(record)
                
                await session.commit()

        except Exception as e:
            print(f"⚠️ Falha processando {filename}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    daemon = SentinelDaemon()
    try:
        asyncio.run(daemon.run_forever())
    except KeyboardInterrupt:
        print("🛑 Sentinel parado pelo usuário.")
