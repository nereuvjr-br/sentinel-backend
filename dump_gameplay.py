import paramiko
from app.core.config import settings

def dump():
    print("🕵️ Dumping Gameplay Log...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(settings.SFTP_HOST, int(settings.SFTP_PORT), settings.SFTP_USER, settings.SFTP_PASS)
        sftp = ssh.open_sftp()
        
        files = sftp.listdir(settings.SFTP_PATH)
        gameplay = [f for f in files if "gameplay" in f and f.endswith('.log')]
        target = sorted(gameplay)[-1]
        
        with sftp.open(f"{settings.SFTP_PATH}/{target}", 'rb') as f:
             content = f.read()
        
        decoded = ""
        for enc in ['utf-16le', 'utf-8', 'latin-1']:
            try:
                decoded = content.decode(enc)
                break
            except: continue
        
        print(f"--- CONTENT OF {target} ---")
        for line in decoded.splitlines()[:50]:
            print(line)

    finally:
        ssh.close()

if __name__ == "__main__":
    dump()
