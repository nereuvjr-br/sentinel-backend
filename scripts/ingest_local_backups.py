import asyncio
import os
import logging
from sentinel_v2 import SentinelDaemonV2
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(level=logging.INFO)
# Un-silence SQL slightly for progress, or keep silent for speed
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

async def ingest_backups():
    BACKUP_DIR = r"C:\Servers\logs\logs\novos"
    
    if not os.path.exists(BACKUP_DIR):
        print(f"❌ Detectado erro: Diretório de backup não encontrado: {BACKUP_DIR}")
        return

    print(f"🚀 Iniciando Ingestão de Backup Local: {BACKUP_DIR}")
    
    daemon = SentinelDaemonV2()
    
    # Get all files .log
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".log")]
    files.sort() # Important to process in chronological order
    
    total_files = len(files)
    print(f"📦 Total de arquivos encontrados: {total_files}")
    
    async with AsyncSession(engine) as session:
        for idx, filename in enumerate(files):
            file_path = os.path.join(BACKUP_DIR, filename)
            file_size = os.path.getsize(file_path)
            
            # Use the existing daemon logic which handles:
            # - Helper methods for parsing
            # - Checksum/Offset (will start from 0 since we wiped DB)
            # - WIPE_DATE filtering
            
            # We bypass the 'process_logs' SFTP loop and call ingest directly
            # But wait, ingest_file expects 'sftp' object to read.
            # We implemented `ingest_local_file` in SentinelDaemonV2 specifically for this!
            
            # Check if file has been processed (should be clean due to wipe)
            pf = await daemon.get_processed_state(session, filename)
            offset = pf.processed_bytes if pf else 0
            
            if file_size > offset:
                print(f"[{idx+1}/{total_files}] Processando {filename}...")
                await daemon.ingest_local_file(session, file_path, filename, offset, file_size)
            else:
                print(f"[{idx+1}/{total_files}] Skipping {filename} (Already processed)")

    print("✅ Ingestão de Backup Local Concluída!")

if __name__ == "__main__":
    asyncio.run(ingest_backups())
