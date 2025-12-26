import paramiko
import re
from app.core.config import settings

def get_first_timestamp(sftp, filepath):
    """
    Reads the first valid timestamp from the log file.
    Assumes standard SCUM log format: YYYY.MM.DD-HH.MM.SS: ...
    """
    try:
        with sftp.open(filepath, 'r') as f:
            # Read first 5 lines to find a timestamp (header might be present)
            for _ in range(5):
                line = f.readline()
                if not line: break
                
                # Regex for timestamp at start of line
                match = re.match(r"^(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2})", line)
                if match:
                    return match.group(1)
                
                # Try UTF-16LE if nonsense (though paramiko 'r' mode might assume utf-8/ascii)
                # Actually paramiko open returns bytes in default 'r' mode usually? 
                # No, standard is binary 'rb' or text 'r'. Let's use 'rb' and decode to be safe against encoding issues.
    except Exception as e:
        return f"Error reading: {e}"
    
    # Retry with 'rb' manual decoding if 'r' failed or yielded nothing
    try:
        with sftp.open(filepath, 'rb') as f:
            head = f.read(1024)
            for enc in ['utf-16le', 'utf-8', 'latin-1']:
                try:
                    decoded = head.decode(enc)
                    match = re.search(r"(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2})", decoded)
                    if match:
                        return match.group(1)
                except: continue
    except:
        pass
        
    return "No timestamp found"

def main():
    print(f"🔌 Connecting to SFTP: {settings.SFTP_HOST}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(settings.SFTP_HOST, int(settings.SFTP_PORT), settings.SFTP_USER, settings.SFTP_PASS)
        sftp = ssh.open_sftp()
        
        print(f"📂 Listing files in {settings.SFTP_PATH}...")
        files = sftp.listdir(settings.SFTP_PATH)
        
        # Filter and Sort
        # We want the OLDEST file for each category to see how far back they go.
        categories = ['login', 'kill', 'chat', 'admin', 'economy']
        earliest_dates = {}
        
        for cat in categories:
            # Find files matching category
            cat_files = [f for f in files if cat in f and f.endswith('.log')]
            cat_files.sort() # lexicographical sort works for YYYYMMDD filenames
            
            if not cat_files:
                earliest_dates[cat] = "No files found"
                continue
                
            oldest_file = cat_files[0]
            # newest_file = cat_files[-1]
            
            ts = get_first_timestamp(sftp, f"{settings.SFTP_PATH}/{oldest_file}")
            earliest_dates[cat] = {
                "file": oldest_file,
                "first_timestamp": ts
            }
            
        print("\n--- 🔍 SFTP Log Retention Analysis ---")
        for cat, data in earliest_dates.items():
            if isinstance(data, str):
                print(f"[{cat.upper()}] {data}")
            else:
                print(f"[{cat.upper()}] Oldest File: {data['file']}")
                print(f"    └── First Data Point: {data['first_timestamp']}")

        sftp.close()
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
