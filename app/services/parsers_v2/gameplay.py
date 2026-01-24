import re
from datetime import datetime
from typing import Optional, Union
from app.models.gameplay_v2 import SentinelRaidMinigame, SentinelCrafting, SentinelExplosiveEvent, SentinelBunkerEvent
from app.models.economy_v2 import SentinelUnparsedLog

from app.services.parsers_v2.utils import extract_user_id

class GameplayParserV2:
    # Existing Regexes - IMPROVED
    # Handle optional Owner with more flexibility: 123([SteamID] Name) OR 123 (Name)
    REGEX_MINIGAME = re.compile(r"(?P<timestamp>[\d\.-]+): \[LogMinigame\] \[(?P<minigame>.*?)\] User: (?P<atk_name>.*?) \(\d+, (?P<atk_id>[\w:]+)\)\. Success: (?P<success>Yes|No)\. Elapsed time: (?P<time>[\d\.]+)\. Failed attempts: (?P<failed>\d+)\. Target object: (?P<target>.*?)\(ID:.*?(?:Lock type: (?P<lock>.*?)\.)? User owner: (?:(?P<owner_id_raw>\d+)\s*\((?:\[(?P<def_id>[\w:]+)\]\s*)?(?P<def_name>.*?)\)|N/A).*Location: X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)")
    
    REGEX_CRAFTING = re.compile(r"(?P<timestamp>[\d\.-]+): \[LogCrafting\] User: (?P<name>.*?) \(\d+, (?P<steam_id>[\w:]+)\)\. Item: (?P<item>.*?) Count: (?P<count>\d+) Location: X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)")

    # New Regexes
    # 2025.12.21-19.34.02: [LogExplosives] User: Player(123) Action: Armed Item: C4 Location: X=...
    REGEX_EXPLOSIVES = re.compile(r"(?P<timestamp>[\d\.-]+): \[LogExplosives\] User: (?P<name>.*?) \(\d+, (?P<steam_id>[\w:]+)\) Action: (?P<action>.*?) Item: (?P<item>.*?) Location: X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)")

    # 2025.12.23-06.01.36: [LogBunkerLock] C4 Bunker is Active. Activated ... X=...
    REGEX_BUNKER = re.compile(r"(?P<timestamp>[\d\.-]+): \[LogBunkerLock\] (?P<bunker>.*?) (?:is|Activated) (?P<status>Active|Locked|Activated).*?(?:X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+))?")

    @staticmethod
    def parse(line: str) -> Union[SentinelRaidMinigame, SentinelCrafting, SentinelExplosiveEvent, SentinelBunkerEvent, SentinelUnparsedLog, None]:
        line = line.strip()
        
        if "[LogMinigame]" in line:
            match = GameplayParserV2.REGEX_MINIGAME.search(line)
            if match:
                data = match.groupdict()
                
                # Handle simplified Owner format (123(Name) without SteamID)
                target_steam = extract_user_id(data.get("def_id"))
                # If def_id is missing but owner_id_raw exists (e.g. log format changed), 
                # we might want to store owner_id_raw or use it. 
                # Currently model only has target_owner_steam_id.
                
                return SentinelRaidMinigame(
                    timestamp=GameplayParserV2._ts(data["timestamp"]),
                    attacker_steam_id=extract_user_id(data["atk_id"]),
                    attacker_name=data["atk_name"].strip(),
                    target_owner_steam_id=target_steam,
                    target_owner_name=data.get("def_name").strip() if data.get("def_name") else None,
                    minigame_class=data["minigame"].strip(),
                    target_object=data["target"].strip(),
                    lock_type=data.get("lock").strip() if data.get("lock") else None,
                    is_success=(data["success"] == "Yes"),
                    failed_attempts=int(data["failed"]),
                    elapsed_time=float(data["time"]),
                    location={"x": float(data['x']), "y": float(data['y']), "z": float(data['z'])}
                )
            else:
                return SentinelUnparsedLog(
                    log_type="Gameplay",
                    filename="unknown", # Filled by caller
                    raw_line=line,
                    attempted_parsers="GameplayParserV2",
                    error_message="Regex mismatch for [LogMinigame]"
                )

        if "[LogCrafting]" in line:
            match_c = GameplayParserV2.REGEX_CRAFTING.search(line)
            if match_c:
                data = match_c.groupdict()
                return SentinelCrafting(
                    timestamp=GameplayParserV2._ts(data["timestamp"]),
                    crafter_steam_id=extract_user_id(data["steam_id"]),
                    crafter_name=data["name"].strip(),
                    item_class=data["item"].strip(),
                    count=int(data["count"]),
                    location={"x": float(data['x']), "y": float(data['y']), "z": float(data['z'])}
                )
            else:
                return SentinelUnparsedLog(
                    log_type="Gameplay",
                    filename="unknown",
                    raw_line=line,
                    attempted_parsers="GameplayParserV2",
                    error_message="Regex mismatch for [LogCrafting]"
                )

        if "[LogExplosives]" in line:
            match_e = GameplayParserV2.REGEX_EXPLOSIVES.search(line)
            if match_e:
                data = match_e.groupdict()
                return SentinelExplosiveEvent(
                    timestamp=GameplayParserV2._ts(data["timestamp"]),
                    steam_id=extract_user_id(data["steam_id"]),
                    player_name=data["name"].strip(),
                    action=data["action"].strip(),
                    item_class=data["item"].strip(),
                    location={"x": float(data['x']), "y": float(data['y']), "z": float(data['z'])}
                )
            else:
                return SentinelUnparsedLog(
                    log_type="Gameplay",
                    filename="unknown",
                    raw_line=line,
                    attempted_parsers="GameplayParserV2",
                    error_message="Regex mismatch for [LogExplosives]"
                )

        if "[LogBunkerLock]" in line:
            match_b = GameplayParserV2.REGEX_BUNKER.search(line)
            if match_b:
                data = match_b.groupdict()
                loc = None
                if data.get('x'):
                    loc = {"x": float(data['x']), "y": float(data['y']), "z": float(data['z'])}
                
                return SentinelBunkerEvent(
                    timestamp=GameplayParserV2._ts(data["timestamp"]),
                    bunker_name=data["bunker"].strip(),
                    action=data["status"].strip(),
                    location=loc
                )
            else:
                return SentinelUnparsedLog(
                    log_type="Gameplay",
                    filename="unknown",
                    raw_line=line,
                    attempted_parsers="GameplayParserV2",
                    error_message="Regex mismatch for [LogBunkerLock]"
                )
                
        return None

    @staticmethod
    def _ts(ts_str: str):
        try:
            return datetime.strptime(ts_str, "%Y.%m.%d-%H.%M.%S")
        except:
            # Fallback for weird timestamps?
            return datetime.utcnow()

