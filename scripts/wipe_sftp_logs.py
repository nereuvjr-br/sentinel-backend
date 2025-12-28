
import paramiko
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sftp_wipe")

def wipe_sftp_logs():
    logger.warning(f"⚠️ WIPING SFTP LOGS ON {settings.SFTP_HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(settings.SFTP_HOST, int(settings.SFTP_PORT), settings.SFTP_USER, settings.SFTP_PASS)
        sftp = ssh.open_sftp()
        
        # Target Directory
        target_dir = '/138.199.5.114_7122/SCUM/Saved/SaveFiles/Logs'
        
        try:
            files = sftp.listdir(target_dir)
            logger.info(f"files found: {len(files)}")
            
            for f in files:
                if f in ['.', '..']: continue
                full_path = f"{target_dir}/{f}"
                try:
                    sftp.remove(full_path)
                    logger.info(f"Deleted: {f}")
                except Exception as e:
                    logger.error(f"Failed to delete {f}: {e}")
                    
        except FileNotFoundError:
            logger.error(f"Directory not found: {target_dir}")
            
    except Exception as e:
        logger.error(f"SFTP Error: {e}")
    finally:
        ssh.close()
        logger.info("SFTP Wipe attempt finished.")

if __name__ == "__main__":
    wipe_sftp_logs()
