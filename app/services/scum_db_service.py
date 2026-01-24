import os
import sqlite3
import paramiko
import asyncio
import tempfile
from datetime import datetime, timezone
from sqlmodel import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logger import logger
from app.core.database import engine
from app.models.players_registry_v2 import SentinelPlayerRegistry, SentinelNameChange
from app.models.clan_v2 import SentinelClan, SentinelClanMember

class ScumDbSyncService:
    def __init__(self):
        self.host = settings.SFTP_HOST
        self.port = int(settings.SFTP_PORT)
        self.username = settings.SFTP_USER
        self.password = settings.SFTP_PASS
        # Caminho absoluto para o SCUM.db baseado no request do usuário
        # "dentro de /138.199.5.114_7122/SaveFiles no sftp tem o arquivo SCUM.db"
        self.remote_db_path = "/138.199.5.114_7122/SaveFiles/SCUM.db"
        self.local_temp_path = os.path.join(tempfile.gettempdir(), "SCUM_SYNC.db")

    async def run_sync_loop(self):
        logger.info(f"🔄 Iniciando Serviço de Sincronização SCUM.db (Intervalo: {settings.SCUM_DB_SYNC_MINUTES} min)")
        while True:
            try:
                await self.sync_routine()
            except Exception as e:
                logger.error(f"❌ Erro no ciclo de sync do SCUM.db: {e}")
            
            await asyncio.sleep(settings.SCUM_DB_SYNC_MINUTES * 60)

    async def sync_routine(self):
        logger.info("📥 Baixando SCUM.db...")
        
        # Run blocking download in thread
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(None, self._download_db_sync)
        
        if not success:
            return

        logger.info("📂 Processando SQLite SCUM.db...")
        try:
            # Run blocking SQLite operations in a thread
            data = await loop.run_in_executor(None, self._extract_sqlite_data)
            
            if data:
                players, clans, members = data
                await self._update_postgres(players, clans, members)
                
        except Exception as e:
            logger.error(f"Erro ao processar SQLite: {e}")

    def _download_db_sync(self):
        if os.path.exists(self.local_temp_path):
            try:
                os.remove(self.local_temp_path)
            except:
                pass

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            logger.info(f"Connecting to SFTP {self.host}...")
            ssh.connect(self.host, self.port, self.username, self.password, timeout=60, banner_timeout=60)
            sftp = ssh.open_sftp()
            
            # Check remote file size
            try:
                stat = sftp.stat(self.remote_db_path)
                remote_size = stat.st_size
                logger.info(f"Remote DB Size: {remote_size / (1024*1024):.2f} MB")
            except Exception as e:
                logger.error(f"Could not stat remote file: {e}")
                return False

            # Custom callback for progress (optional, but good for debugging)
            def progress(transferred, total):
                if transferred % (10 * 1024 * 1024) == 0:  # Log every 10MB
                    logger.info(f"Downloading SCUM.db: {transferred/total*100:.1f}% ({transferred//(1024*1024)}mb)")

            sftp.get(self.remote_db_path, self.local_temp_path, callback=progress)
            
            sftp.close()
            ssh.close()
            
            # Verify local size
            local_size = os.path.getsize(self.local_temp_path)
            if local_size != remote_size:
                logger.warning(f"⚠️ Tamanho do arquivo mudou durante download (Live DB). Local: {local_size} != Remote: {remote_size}. Tentando processar mesmo assim.")
                # return False  <-- Allow proceeding
                
            logger.info("✅ Download do SCUM.db concluído com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Falha ao baixar SCUM.db via SFTP: {e}")
            return False
            
    def _extract_sqlite_data(self):
        """Função síncrona para ler SQLite e retornar dados brutos"""
        conn = sqlite3.connect(self.local_temp_path)
        cursor = conn.cursor()
        
        # 1. Obter Tabelas Relevantes
        try:
            # --- PLAYERS (user_profile) ---
            # user_id = SteamID, name = ScumName
            cursor.execute('SELECT user_id, name FROM user_profile')
            scum_players = cursor.fetchall()
            
            # --- CLANS (squad) ---
            # Columns: id, name, information (desc), member_limit
            cursor.execute('SELECT id, name, information, member_limit FROM squad')
            scum_clans = cursor.fetchall()
            
            # --- CLAN MEMBERS (squad_member) ---
            # Join squad_member with user_profile to get SteamID
            cursor.execute('''
                SELECT m.squad_id, u.user_id, m.rank 
                FROM squad_member m
                JOIN user_profile u ON m.user_profile_id = u.id
            ''')
            scum_members = cursor.fetchall()
            
            conn.close()
            return scum_players, scum_clans, scum_members
            
        except sqlite3.OperationalError as e:
            logger.error(f"Erro de Schema no SQLite (tabelas mudaram?): {e}")
            conn.close()
            return None
    
    async def _update_postgres(self, players, clans, members):
        async with AsyncSession(engine) as session:
            try:
                # 1. Upsert Players
                count = 0
                for p_steam_id, p_name in players:
                    if not p_steam_id: continue
                    
                    # Normalizar
                    p_steam_id = str(p_steam_id)
                    p_name = str(p_name) if p_name else "Unknown"
                    
                    stmt = select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.steam_id == p_steam_id)
                    result = await session.execute(stmt)
                    existing_player = result.scalar_one_or_none()
                    
                    if existing_player:
                        # Check for name change
                        if p_name and existing_player.current_name != p_name:
                            # Record name change
                            name_change = SentinelNameChange(
                                steam_id=p_steam_id,
                                old_name=existing_player.current_name,
                                new_name=p_name,
                                changed_at=datetime.utcnow(),
                                detected_in="scum_db_sync"
                            )
                            session.add(name_change)
                            
                            # Update current name
                            existing_player.current_name = p_name
                            session.add(existing_player)
                            logger.info(f"🔄 Name change detected (SCUM.db): {name_change.old_name} -> {p_name}")
                    else:
                        new_player = SentinelPlayerRegistry(
                            steam_id=p_steam_id,
                            current_name=p_name,
                            first_seen=datetime.utcnow(),
                            last_seen=datetime.utcnow()
                        )
                        session.add(new_player)
                        
                    # Batch commit every 100 players
                    count += 1
                    if count % 100 == 0:
                        await session.commit()
                
                await session.commit()
                
                # 2. Sync Clans
                clan_map = {} 
                
                # Unpack clans (id, name, desc, limit) - LeaderID removed
                for c_id, c_name, c_desc, c_limit in clans:
                    clan_map[c_id] = c_name
                    
                    stmt = select(SentinelClan).where(SentinelClan.scum_clan_id == c_id)
                    result = await session.execute(stmt)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        existing.name = c_name
                        existing.description = c_desc
                        # existing.member_count updated later hopefully or strictly here?
                        session.add(existing)
                    else:
                        new_clan = SentinelClan(
                            scum_clan_id=c_id,
                            name=c_name,
                            description=c_desc,
                            member_count=0 
                        )
                        session.add(new_clan)
                    
                await session.commit()
                
                # 3. Sync Members & Relations
                await session.execute(delete(SentinelClanMember))
                
                # Count members per clan for update
                clan_counts = {}

                for c_id, m_steam_id, m_rank in members:
                    if not m_steam_id: continue
                    m_steam_id = str(m_steam_id)
                    
                    new_member = SentinelClanMember(
                        clan_id=c_id,
                        steam_id=m_steam_id,
                        rank=str(m_rank)
                    )
                    session.add(new_member)
                    
                    # Count
                    clan_counts[c_id] = clan_counts.get(c_id, 0) + 1
                    
                    # Atualizar PlayerRegistry com info do Clan
                    stmt = select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.steam_id == m_steam_id)
                    res = await session.execute(stmt)
                    player = res.scalar_one_or_none()
                    if player:
                        player.squad_name = clan_map.get(c_id, "Unknown")
                        session.add(player)
                
                await session.commit()
                
                # Update Member Counts in Clans
                for c_id, count in clan_counts.items():
                    stmt = select(SentinelClan).where(SentinelClan.scum_clan_id == c_id)
                    res = await session.execute(stmt)
                    clan = res.scalar_one_or_none()
                    if clan:
                        clan.member_count = count
                        session.add(clan)
                
                await session.commit()
                logger.info("✅ Sync SCUM.db concluído com sucesso!")
                
            except Exception as e:
                logger.error(f"Erro no Update Postgres: {e}")
                await session.rollback()

scum_db_service = ScumDbSyncService()
