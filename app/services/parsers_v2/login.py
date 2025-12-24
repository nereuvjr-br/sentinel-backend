import re
from datetime import datetime
from typing import Optional
from app.models.login_v2 import SentinelLogin

class LoginParserV2:
    # 2025.12.21-16.05.29: '...' logged in at: X=... Y=... Z=...
    # 2025.12.21-00.01.31: '...' logged out at: ?
    REGEX_LOGIN = re.compile(r"(?P<timestamp>[\d\.-]+): '(?P<ip>[\d\.]+) (?P<steam_id>\d+):(?P<name>.*?)\((?P<game_id>\d+)\)' (?P<action>logged in|logged out) at: (?:X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)|\?)(?P<extra>.*)")

    @staticmethod
    def parse(line: str) -> Optional[SentinelLogin]:
        line = line.strip()
        match = LoginParserV2.REGEX_LOGIN.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        
        # Check Drone
        l_type = "Standard"
        if "(as drone)" in data.get("extra", ""):
            l_type = "Drone"
            
        action_map = {
            "logged in": "Login",
            "logged out": "Logout"
        }
        
        location = None
        if data.get('x') and data.get('y'):
            location = {
                "x": float(data['x']), 
                "y": float(data['y']), 
                "z": float(data['z'])
            }

        return SentinelLogin(
            timestamp=LoginParserV2._ts(data["timestamp"]),
            ip_address=data["ip"],
            steam_id=data["steam_id"],
            player_name=data["name"],
            game_id=int(data["game_id"]),
            action=action_map.get(data["action"], "Unknown"),
            login_type=l_type,
            location=location
        )

    @staticmethod
    def _ts(ts_str: str):
        try:
            return datetime.strptime(ts_str, "%Y.%m.%d-%H.%M.%S")
        except:
            return datetime.utcnow()
