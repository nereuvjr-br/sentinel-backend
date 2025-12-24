import re
from datetime import datetime
from typing import Optional
from app.models.violation_v2 import SentinelViolation

class ViolationParserV2:
    # 2025.12.21-19.18.56: [AmmoCountMismatch] Ammo count violation detected: Weapon: Weapon_MK18, PrisonerLocation: X=-420561.062 Y=-11397.580 Z=35108.961, Count: 1, SuspiciousCount: 31, BanCount: 61, User: Dark (101, 76561198449280484), 
    REGEX_CHEAT = re.compile(r"(?P<timestamp>[\d\.-]+): \[(?P<type>.*?)\] (?P<desc>.*?): (?:Weapon: (?P<wep>.*?), )?(?:PrisonerLocation: (?P<loc>.*?), )?.*SuspiciousCount: (?P<susp>\d+), BanCount: (?P<ban>\d+), User: (?P<name>.*?) \(\d+, (?P<steam_id>\d+)\)")

    # 2025.12.21-18.05.01: AConZGameMode::KickPlayer: User id: '76561198253286676', Reason: NetErrorUnauthorized
    REGEX_KICK = re.compile(r"(?P<timestamp>[\d\.-]+): AConZGameMode::KickPlayer: User id: '(?P<steam_id>\d+)', Reason: (?P<reason>.*)")

    @staticmethod
    def parse(line: str) -> Optional[SentinelViolation]:
        line = line.strip()
        
        # --- CHEAT (WITH COUNTERS) ---
        if "[" in line and "User:" in line:
            # Try specific counters regex first
            match = ViolationParserV2.REGEX_CHEAT.search(line)
            if match:
                data = match.groupdict()
                
                # Parse Loc "X=... Y=... Z=..."
                loc = None
                if data.get("loc"):
                    try:
                        parts = data["loc"].split()
                        x = float(parts[0].split('=')[1])
                        y = float(parts[1].split('=')[1])
                        z = float(parts[2].split('=')[1])
                        loc = {"x": x, "y": y, "z": z}
                    except:
                        pass

                return SentinelViolation(
                    timestamp=ViolationParserV2._ts(data["timestamp"]),
                    steam_id=data["steam_id"],
                    player_name=data["name"],
                    violation_class=data["type"],
                    description=data["desc"],
                    weapon=data.get("wep"),
                    location=loc,
                    suspicious_count=int(data["susp"]),
                    ban_count=int(data["ban"])
                )
            
            # Fallback: Generic Regex for violations without counters (e.g. OutOfInteractionRange)
            # 2025.12.21-00.06.35: [OutOfInteractionRange] ... User: Name (ID, SteamID),
            REGEX_GENERIC = re.compile(r"(?P<timestamp>[\d\.-]+): \[(?P<type>.*?)\] (?P<desc>.*?): .*?User: (?P<name>.*?) \(\d+, (?P<steam_id>\d+)\)")
            match_g = REGEX_GENERIC.search(line)
            if match_g:
                data = match_g.groupdict()
                return SentinelViolation(
                    timestamp=ViolationParserV2._ts(data["timestamp"]),
                    steam_id=data["steam_id"],
                    player_name=data["name"],
                    violation_class=data["type"],
                    description=data["desc"],
                    suspicious_count=0,
                    ban_count=0
                )

        # --- KICK ---
        if "KickPlayer" in line:
            match_k = ViolationParserV2.REGEX_KICK.search(line)
            if match_k:
                data = match_k.groupdict()
                return SentinelViolation(
                    timestamp=ViolationParserV2._ts(data["timestamp"]),
                    steam_id=data["steam_id"],
                    player_name="Unknown (Kick)",
                    violation_class="ServerKick",
                    description=f"Kicked for {data['reason']}",
                    suspicious_count=0,
                    ban_count=0
                )
                
        return None

    @staticmethod
    def _ts(ts_str: str):
        try:
            return datetime.strptime(ts_str, "%Y.%m.%d-%H.%M.%S")
        except:
            return datetime.utcnow()
