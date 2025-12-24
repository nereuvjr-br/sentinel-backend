import paramiko
from app.core.config import settings
from app.services.parsers_v2.admin import AdminParserV2

def debug():
    print("🕵️ Debugging Admin Log...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(settings.SFTP_HOST, int(settings.SFTP_PORT), settings.SFTP_USER, settings.SFTP_PASS)
        sftp = ssh.open_sftp()
        
        # Find latest admin log
        files = sftp.listdir(settings.SFTP_PATH)
        admin_files = [f for f in files if "admin" in f]
        admin_files.sort()
        
        target = admin_files[-1]
        print(f"Target: {target}")
        
        with sftp.open(f"{settings.SFTP_PATH}/{target}", 'rb') as f:
             content = f.read()
        
        # Decode strategy
        decoded = ""
        for enc in ['utf-16le', 'utf-8', 'latin-1']:
            try:
                decoded = content.decode(enc)
                break
            except: continue
            
        print(f"Decoded {len(decoded)} chars.")
        
        success = 0
        fail = 0
        
        for line in decoded.splitlines():
            if not line.strip(): continue
            res = AdminParserV2.parse(line)
            if res:
                success += 1
            else:
                fail += 1
                if fail < 10: # Sample failures
                    print(f"❌ FAIL: {line[:100]}...")
                    
        print(f"Result: {success} OK, {fail} IGNORED.")

    finally:
        ssh.close()

if __name__ == "__main__":
    debug()
