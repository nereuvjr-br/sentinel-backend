import asyncio
import os
import paramiko
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession

# Core Config
from app.core.config import settings
from app.core.database import engine

# Models
from app.models.system_v2 import SentinelProcessedFile
from app.models.admin_v2 import SentinelAdminCommand
from app.models.chat_v2 import SentinelChatMessage
from app.models.login_v2 import SentinelLogin
from app.models.kill_v2 import SentinelKill
from app.models.economy_v2 import (
    SentinelEconomyTrade, 
    SentinelEconomyBalance,
    SentinelBankTransaction,
    SentinelMechanicService,
    SentinelBankCard,
    SentinelUnparsedLog
)
from app.models.gameplay_v2 import SentinelRaidMinigame, SentinelCrafting
from app.models.violation_v2 import SentinelViolation
from app.models.chest_fame_v2 import SentinelChestEvent, SentinelFameEvent

# Parsers
from app.services.parsers_v2.admin import AdminParserV2
from app.services.parsers_v2.chat import ChatParserV2
from app.services.parsers_v2.login import LoginParserV2
from app.services.parsers_v2.kill import KillParserV2
from app.services.parsers_v2.economy import EconomyParserV2
from app.services.parsers_v2.gameplay import GameplayParserV2
from app.services.parsers_v2.violation import ViolationParserV2
from app.services.parsers_v2.chest_fame import ChestFameParserV2

class SentinelDaemonV2:
    def __init__(self):
        self.host = settings.SFTP_HOST
        self.port = int(settings.SFTP_PORT)
        self.username = settings.SFTP_USER
        self.password = settings.SFTP_PASS
        self.remote_dir = settings.SFTP_PATH
        self.batch_size = 100
        
        self.wipe_date = None
        if settings.WIPE_DATE:
            try:
                # Handle potential "Z" or differing formats if needed, but fromisoformat is robust for generated strings
                dt = datetime.fromisoformat(settings.WIPE_DATE)
                # Ensure correct timezone if naive
                if dt.tzinfo is None:
                    try:
                        tz = ZoneInfo(settings.TIMEZONE)
                    except:
                        tz = timezone.utc
                    dt = dt.replace(tzinfo=tz)
                
                # Convert to UTC for internal comparison
                self.wipe_date = dt.astimezone(timezone.utc)
                print(f"📅 WIPE FILTER ACTIVE: Ignorando dados antes de {self.wipe_date} (Configurado: {settings.WIPE_DATE} {settings.TIMEZONE})")
            except Exception as e:
                print(f"⚠️ Erro ao parsear WIPE_DATE: {e}")

    async def run(self):
        print(f"🚀 Sentinel V2 (Tailing Mode) Iniciado. Monitorando {self.host}...")
        
        while True:
            try:
                await self.process_logs()
                print("💤 Ciclo de Scan concluído. Dormindo 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"❌ Erro Crítico no Loop:")
                print(error_trace)
                
                # Save to DB for frontend monitoring
                try:
                    async with AsyncSession(engine) as session:
                        log = SentinelUnparsedLog(
                            log_type="SYSTEM_ERROR",
                            filename="sentinel_v2.py",
                            raw_line=error_trace,
                            error_message=str(e),
                            attempted_parsers="daemon_loop"
                        )
                        session.add(log)
                        await session.commit()
                except:
                    print("Could not save system error to DB.")
                
                await asyncio.sleep(30)

    async def process_logs(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(self.host, self.port, self.username, self.password)
            sftp = ssh.open_sftp()
            
            # List with Attributes for size check
            # sftp.listdir_attr returns SFTPAttributes objects
            file_attrs = sftp.listdir_attr(self.remote_dir)
            files = [(f.filename, f.st_size) for f in file_attrs if f.filename.endswith('.log')]
            files.sort()
            
            async with AsyncSession(engine) as session:
                for filename, remote_size in files:
                    # Check DB state
                    pf = await self.get_processed_state(session, filename)
                    local_offset = pf.processed_bytes if pf else 0
                    
                    if remote_size > local_offset:
                        print(f"📂 Tailing {filename} (Size: {remote_size} > Offset: {local_offset})")
                        await self.ingest_file(session, sftp, filename, local_offset, remote_size)
                    elif not pf:
                        # New File case (if size 0?)
                         await self.ingest_file(session, sftp, filename, 0, remote_size)
                    else:
                        pass # print(f"⏭️ Skipping {filename} (Up to date)")
                    
        finally:
            ssh.close()

    async def get_processed_state(self, session, filename):
        stmt = select(SentinelProcessedFile).where(SentinelProcessedFile.filename == filename)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def ingest_file(self, session, sftp, filename, offset, current_size):
        file_path = f"{self.remote_dir}/{filename}"
        
        # Determine Type and Parser
        parser_func = None
        log_type = "Unknown"
        
        if "admin" in filename: parser_func = AdminParserV2.parse; log_type="Admin"
        elif "chat" in filename: parser_func = ChatParserV2.parse; log_type="Chat"
        elif "login" in filename: parser_func = LoginParserV2.parse; log_type="Login"
        elif "kill" in filename: parser_func = KillParserV2.parse; log_type="Kill"
        elif "economy" in filename: parser_func = EconomyParserV2.parse; log_type="Economy"
        elif "gameplay" in filename: parser_func = GameplayParserV2.parse; log_type="Gameplay"
        elif "violations" in filename: parser_func = ViolationParserV2.parse; log_type="Violation"
        elif "chest" in filename: parser_func = ChestFameParserV2.parse_chest; log_type="Chest"
        elif "famepoints" in filename: parser_func = ChestFameParserV2.parse_fame; log_type="Fame"
        elif "vehicle" in filename: parser_func = lambda x: None; log_type="Vehicle" # Placeholder

        if not parser_func:
            return

        batch = []
        new_lines_count = 0
        
        try:
            with sftp.open(file_path, 'rb') as f:
                f.seek(offset)
                content = f.read(current_size - offset) # Read only new content
                
            decoded = ""
            # SCUM logs change encoding.
            # Warning: Tailing UTF-16 in chunks can be dangerous if we split a character.
            # But since we read until EOF (current_size), logic normally holds unless a rename/rotation happens mid-read.
            encodings = ['utf-16le', 'utf-8', 'latin-1']
            
            for enc in encodings:
                try:
                    decoded = content.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            
            if not decoded:
                decoded = content.decode('utf-8', errors='replace')

            for line in decoded.splitlines():
                if not line.strip(): continue
                model = parser_func(line)
                if model:
                    # Preenche filename se for unparsed log
                    if isinstance(model, SentinelUnparsedLog):
                        model.filename = filename
                    
                    # --- Timezone Normalization & Filtering ---
                    if not isinstance(model, SentinelUnparsedLog) and hasattr(model, 'timestamp'):
                        # 1. Normalize to Aware UTC (for logic)
                        if model.timestamp.tzinfo is None:
                            model.timestamp = model.timestamp.replace(tzinfo=timezone.utc)
                        
                        # Ensure it's in UTC
                        model.timestamp = model.timestamp.astimezone(timezone.utc)
                        
                        # 2. Wipe Date Filter
                        if self.wipe_date and model.timestamp < self.wipe_date:
                            continue
                            
                        # 3. Prepare for DB (Strip Timezone -> Naive UTC)
                        # SQLAlchemy/asyncpg often prefer Naive timestamps for DateTime columns
                        # to avoid "can't subtract offset-naive" errors during parameter binding/adaptation.
                        model.timestamp = model.timestamp.replace(tzinfo=None)
                        
                    batch.append(model)
                    new_lines_count += 1
                
                if len(batch) >= self.batch_size:
                    session.add_all(batch)
                    await session.commit()
                    batch = []
            
            if batch:
                session.add_all(batch)
                await session.commit()

            # Update State with NEW TOTAL SIZE
            # We use merge to insert or update
            pf = await self.get_processed_state(session, filename)
            if not pf:
                pf = SentinelProcessedFile(filename=filename, log_type=log_type)
            
            pf.processed_bytes = current_size
            pf.lines_processed += new_lines_count
            pf.last_modified = datetime.utcnow()
            
            session.add(pf)
            await session.commit()
            print(f"✅ Atualizado {filename}: +{new_lines_count} eventos.")

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Erro ao Tailing {filename}:")
            print(error_trace)
            
            # Rollback transaction to clear error state
            await session.rollback()
            
            # Save System Error
            try:
                log = SentinelUnparsedLog(
                    log_type="SYSTEM_ERROR",
                    filename=filename,
                    raw_line=error_trace,
                    error_message=str(e),
                    attempted_parsers=log_type
                )
                session.add(log)
                await session.commit()
            except Exception as e2:
                print(f"Failed to log system error: {e2}")

if __name__ == "__main__":
    daemon = SentinelDaemonV2()
    asyncio.run(daemon.run())
