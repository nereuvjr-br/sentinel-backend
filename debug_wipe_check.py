
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Add backend to path
sys.path.insert(0, '/home/nereu-jr/Área de trabalho/scum/SCUMSentinel/backend')

from app.core.config import settings
from app.services.parsers_v2.economy import EconomyParserV2

def check_logs():
    print(f"Checking logs against WIPE_DATE: {settings.WIPE_DATE}")
    wipe_date = datetime.fromisoformat(settings.WIPE_DATE)
    if wipe_date.tzinfo is None:
        tz = ZoneInfo(settings.TIMEZONE)
        wipe_date = wipe_date.replace(tzinfo=tz)
    
    print(f"Wipe Date (Aware): {wipe_date}")

    log_dir = settings.SFTP_PATH # This is remote path, locally we check where successful downloads go?
    # Usually sentinel downloads to a local folder.
    # Let's check sentinel_v2.py to see where it saves files.
    # Assuming "logs" dir in backend or similar.
    
    local_logs_dir = "logs"
    if not os.path.exists(local_logs_dir):
        print(f"Local logs dir {local_logs_dir} not found.")
        return

    count_valid = 0
    count_total = 0
    
    for filename in os.listdir(local_logs_dir):
        if "economy" in filename and filename.endswith(".log"):
            filepath = os.path.join(local_logs_dir, filename)
            print(f"Checking {filename}...")
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    count_total += 1
                    # Quick pre-check
                    if "[Trade]" not in line and "[Bank]" not in line:
                        continue
                        
                    parsed = EconomyParserV2.parse(line)
                    if parsed:
                        # parse() now returns None if before wipe date
                        # But wait, checking the *file* logic implies I should test if the parse logic WORKS.
                        # Since I modified parse to Return None on old dates, 
                        # if parsed is NOT None, it means it PASSED the check.
                        print(f"  [PASS] Found valid entry: {parsed.timestamp}")
                        count_valid += 1
                        if count_valid >= 5:
                            return
    
    print(f"Total checked lines: {count_total}")
    print(f"Valid entries found: {count_valid}")

if __name__ == "__main__":
    check_logs()
