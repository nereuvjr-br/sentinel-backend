
import asyncio
import paramiko
from app.core.config import settings
from app.core.database import engine
from app.models.system_v2 import SentinelProcessedFile
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

async def deep_sftp_check():
    print("--- DEEP SFTP FILE CHECK ---")
    
    # 1. List Remote Files via SFTP
    print("\n[REMOTE SFTP FILES]")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(settings.SFTP_HOST, int(settings.SFTP_PORT), settings.SFTP_USER, settings.SFTP_PASS)
        sftp = ssh.open_sftp()
        try:
            files = sftp.listdir_attr(settings.SFTP_PATH)
            # Filter Kills logs only, sort by time desc
            kill_files = [(f.filename, f.st_size, f.st_mtime) for f in files if "kill" in f.filename]
            kill_files.sort(key=lambda x: x[0], reverse=True) # Check by name/date
            
            for fname, size, mtime in kill_files[:5]:
                print(f"🌍 Remote: {fname:<30} | Size: {size} bytes")
                
                # Check Local DB State for this file
                async with AsyncSession(engine) as session:
                    pf = (await session.execute(select(SentinelProcessedFile).where(SentinelProcessedFile.filename == fname))).scalars().first()
                    if pf:
                        diff = size - pf.processed_bytes
                        status = "✅ Synced" if diff == 0 else f"⚠️ BEHIND by {diff} bytes"
                        print(f"   💾 Local:  Processed: {pf.processed_bytes} | {status}")
                    else:
                        print(f"   💾 Local:  NOT TRACKED YET (New File)")

        except Exception as e:
            print(f"SFTP List Error: {e}")
        finally:
            sftp.close()
    except Exception as e:
        print(f"SSH Connect Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    asyncio.run(deep_sftp_check())
