import paramiko
from app.core.config import settings
from app.services.parsers_v2.gameplay import GameplayParserV2
from app.services.parsers_v2.chest_fame import ChestFameParserV2

def debug():
    print("🕵️ Debugging Parsers Live...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(settings.SFTP_HOST, int(settings.SFTP_PORT), settings.SFTP_USER, settings.SFTP_PASS)
        sftp = ssh.open_sftp()
        
        files = sftp.listdir(settings.SFTP_PATH)
        
        # --- DEBUG CRAFTING (Gameplay) ---
        gameplay = [f for f in files if "gameplay" in f and f.endswith('.log')]
        if gameplay:
            target = sorted(gameplay)[-1]
            print(f"\n--- Testing Gameplay: {target} ---")
            content = read_remote(sftp, target)
            
            c_craft = 0
            for line in content.splitlines():
                if "Crafting" in line:
                    res = GameplayParserV2.parse(line) # Parse any gameplay line
                    # But parse() returns Raid OR Crafting. 
                    # We need to know if it detected CRAFTING.
                    from app.models.gameplay_v2 import SentinelCrafting
                    if isinstance(res, SentinelCrafting):
                        c_craft += 1
                    else:
                        print(f"❌ MISSED CRAFT: {line[:100]}...")
            print(f"Detected Crafting: {c_craft}")

        # --- DEBUG CHEST ---
        chests = [f for f in files if "chest" in f and f.endswith('.log')]
        if chests:
            target = sorted(chests)[-1]
            print(f"\n--- Testing Chest: {target} ---")
            content = read_remote(sftp, target)
            
            c_chest = 0
            for line in content.splitlines():
                res = ChestFameParserV2.parse_chest(line)
                if res:
                    c_chest += 1
                elif "Chest" in line and "ownership" in line:
                     print(f"❌ MISSED CHEST: {line[:100]}...")
                     
            print(f"Detected Chest: {c_chest}")

    finally:
        ssh.close()

def read_remote(sftp, filename):
    with sftp.open(f"{settings.SFTP_PATH}/{filename}", 'rb') as f:
         content = f.read()
    
    decoded = ""
    for enc in ['utf-16le', 'utf-8', 'latin-1']:
        try:
            decoded = content.decode(enc)
            break
        except: continue
    return decoded or content.decode('utf-8', errors='replace')

if __name__ == "__main__":
    debug()
