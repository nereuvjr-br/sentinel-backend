import paramiko
from app.core.config import settings

def explore():
    print(f"🕵️ Explorando SFTP {settings.SFTP_HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(settings.SFTP_HOST, int(settings.SFTP_PORT), settings.SFTP_USER, settings.SFTP_PASS)
        sftp = ssh.open_sftp()
        
        # Start at root or home
        paths_to_check = ['/138.199.5.114_7122', '/138.199.5.114_7122/SCUM/Saved/SaveFiles/Logs']
        
        for p in paths_to_check:
            try:
                print(f"\n📂 Listing {p}:")
                files = sftp.listdir(p)
                print(files[:10]) # Show first 10
            except Exception as e:
                print(f"❌ {p}: {e}")
                
    except Exception as e:
        print(f"Erro Geral: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    explore()
