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
from app.core.logger import logger

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
                logger.info(f"📅 WIPE FILTER ACTIVE: Ignorando dados antes de {self.wipe_date} (Configurado: {settings.WIPE_DATE} {settings.TIMEZONE})")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao parsear WIPE_DATE: {e}")

    async def run(self):
        logger.info(f"🚀 Sentinel V2 (Tailing Mode) Iniciado. Monitorando {self.host}...")
        
        while True:
            try:
                await self.process_logs()
                logger.debug("💤 Ciclo de Scan concluído. Dormindo 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                logger.critical(f"❌ Erro Crítico no Loop: {error_trace}")
                
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
                    logger.error("Could not save system error to DB.")
                
                await asyncio.sleep(30)

    async def process_logs(self):
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                ssh.connect(self.host, self.port, self.username, self.password, timeout=10)
                sftp = ssh.open_sftp()
                
                try:
                    # List with Attributes for size check
                    file_attrs = sftp.listdir_attr(self.remote_dir)
                    files = [(f.filename, f.st_size) for f in file_attrs if f.filename.endswith('.log')]
                    files.sort()
                    
                    async with AsyncSession(engine) as session:
                        for filename, remote_size in files:
                            # Check DB state
                            pf = await self.get_processed_state(session, filename)
                            local_offset = pf.processed_bytes if pf else 0
                            
                            if remote_size > local_offset:
                                logger.info(f"📂 Tailing {filename} (Size: {remote_size} > Offset: {local_offset})")
                                await self.ingest_file(session, sftp, filename, local_offset, remote_size)
                            elif not pf:
                                # New File case
                                await self.ingest_file(session, sftp, filename, 0, remote_size)
                    
                    # If successful, break retry loop
                    return

                finally:
                    try:
                        sftp.close()
                    except: pass
            
            except (paramiko.SSHException, OSError) as e:
                logger.warning(f"⚠️ SFTP Connection Failed (Attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
            finally:
                ssh.close()
        
        logger.error("❌ Failed to connect to SFTP after multiple attempts.")

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
                # Read only new content
                # For very large files, this `read()` might be too much for memory.
                # ideally we chunk it, but for now we follow the existing pattern for consistency.
                content = f.read(current_size - offset) 
            
            new_lines_count = await self._process_content(session, content, filename, parser_func, log_type)

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
            logger.info(f"✅ Atualizado {filename}: +{new_lines_count} eventos.")

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"❌ Erro ao Tailing {filename}: {error_trace}")
            
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
                logger.error(f"Failed to log system error: {e2}")

    async def _process_content(self, session, content, filename, parser_func, log_type):
        decoded = ""
        # SCUM logs change encoding.
        encodings = ['utf-16le', 'utf-8', 'latin-1']
        
        for enc in encodings:
            try:
                decoded = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        
        if not decoded:
            decoded = content.decode('utf-8', errors='replace')

        batch = []
        new_lines_count = 0

        for line in decoded.splitlines():
            line_clean = line.strip()
            if not line_clean: continue
            
            model = None
            try:
                model = parser_func(line)
            except Exception as pe:
                # Log parser crash logic
                logger.debug(f"Parser Crash on line: {line_clean[:50]}... Error: {pe}")
                # We could log to UnparsedLog here, but let's assume if it returns nothing it's bad
            
            if model:
                # Preenche filename se for unparsed log
                if isinstance(model, SentinelUnparsedLog):
                    model.filename = filename
                
                # --- Timezone Normalization & Filtering ---
                try:
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
                        model.timestamp = model.timestamp.replace(tzinfo=None)
                    
                    batch.append(model)
                    new_lines_count += 1
                except Exception as te:
                    logger.error(f"Timezone/Filter Error: {te}")
                    continue
            
            if len(batch) >= self.batch_size:
                await self._safe_commit_batch(session, batch)
                batch = []
        
        if batch:
            await self._safe_commit_batch(session, batch)
            
        return new_lines_count

    async def _safe_commit_batch(self, session, batch):
        """Tries to commit a batch. If fails, tries individual items."""
        if not batch: return
        
        try:
            session.add_all(batch)
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.warning(f"⚠️ Batch Commit Failed ({len(batch)} items). Retrying individually. Error: {e}")
            
            for item in batch:
                try:
                    session.add(item)
                    await session.commit()
                except Exception as ie:
                    await session.rollback()
                    # Log failed item (Dead Letter)
                    logger.error(f"❌ Dropped Bad Item: {item} | Error: {ie}")
                    # Optionally insert into UnparsedLog table explicitly here

    async def ingest_local_file(self, session, local_path, filename, offset, current_size):
        log_type = self._determine_log_type(filename)
        parser_func = self._get_parser_func(filename)

        if not parser_func:
            return

        try:
            with open(local_path, 'rb') as f:
                f.seek(offset)
                content = f.read(current_size - offset)
            
            new_lines_count = await self._process_content(session, content, filename, parser_func, log_type)
            
            # Update State same as SFTP
            pf = await self.get_processed_state(session, filename)
            if not pf:
                pf = SentinelProcessedFile(filename=filename, log_type=log_type)
            
            pf.processed_bytes = current_size
            pf.lines_processed += new_lines_count
            pf.last_modified = datetime.utcnow()
            
            session.add(pf)
            await session.commit()
            logger.info(f"✅ [LOCAL] Atualizado {filename}: +{new_lines_count} eventos.")

        except Exception as e:
            logger.error(f"❌ Erro ao processar local {filename}: {e}")

    def _determine_log_type(self, filename):
        if "admin" in filename: return "Admin"
        elif "chat" in filename: return "Chat"
        elif "login" in filename: return "Login"
        elif "kill" in filename: return "Kill"
        elif "economy" in filename: return "Economy"
        elif "gameplay" in filename: return "Gameplay"
        elif "violations" in filename: return "Violation"
        elif "chest" in filename: return "Chest"
        elif "famepoints" in filename: return "Fame"
        elif "vehicle" in filename: return "Vehicle"
        return "Unknown"

    def _get_parser_func(self, filename):
        if "admin" in filename: return AdminParserV2.parse
        elif "chat" in filename: return ChatParserV2.parse
        elif "login" in filename: return LoginParserV2.parse
        elif "kill" in filename: return KillParserV2.parse
        elif "economy" in filename: return EconomyParserV2.parse
        elif "gameplay" in filename: return GameplayParserV2.parse
        elif "violations" in filename: return ViolationParserV2.parse
        elif "chest" in filename: return ChestFameParserV2.parse_chest
        elif "famepoints" in filename: return ChestFameParserV2.parse_fame
        elif "vehicle" in filename: return lambda x: None
        return None

if __name__ == "__main__":
    daemon = SentinelDaemonV2()
    asyncio.run(daemon.run())
