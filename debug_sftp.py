import paramiko
import os
from datetime import datetime
from app.core.config import settings

def test_sftp():
    host = settings.SFTP_HOST
    port = int(settings.SFTP_PORT)
    username = settings.SFTP_USER
    password = settings.SFTP_PASS
    remote_dir = settings.SFTP_PATH
    
    print(f"Connecting to {host}:{port} as {username}...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, password, timeout=30)
        sftp = ssh.open_sftp()
        print("✅ Connected!")
        
        print(f"\nConfigured SFTP Path: {remote_dir}")
        target_file = f"{remote_dir}/kill_20260119180057.log"
        print(f"Reading first 20 lines of {target_file}...")
        
        try:
            with sftp.open(target_file, 'rb') as f:
                content = f.read(2048) # Read a chunk
                decoded = content.decode('utf-8', errors='replace')
                lines = decoded.splitlines()[:20]
                for i, line in enumerate(lines):
                    print(f"{i+1}: {line}")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            
        sftp.close()
        ssh.close()
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_sftp()
