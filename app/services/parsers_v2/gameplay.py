import re
from datetime import datetime
from typing import Optional, Union
from app.models.gameplay_v2 import SentinelRaidMinigame, SentinelCrafting, SentinelExplosiveEvent, SentinelBunkerEvent

from app.services.parsers_v2.utils import extract_user_id

class GameplayParserV2:
    # Existing Regexes
    REGEX_MINIGAME = re.compile(r"(?P<timestamp>[\d\.-]+): \[LogMinigame\] \[(?P<minigame>.*?)\] User: (?P<atk_name>.*?) \(\d+, (?P<atk_id>[\w:]+)\)\. Success: (?P<success>Yes|No)\. Elapsed time: (?P<time>[\d\.]+)\. Failed attempts: (?P<failed>\d+)\. Target object: (?P<target>.*?)\(ID:.*?(?:Lock type: (?P<lock>.*?)\.)? User owner: (?:\d+\(\[(?P<def_id>[\w:]+)\] (?P<def_name>.*?)\)|N/A).*Location: X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)")
    REGEX_CRAFTING = re.compile(r"(?P<timestamp>[\d\.-]+): \[LogCrafting\] User: (?P<name>.*?) \(\d+, (?P<steam_id>[\w:]+)\)\. Item: (?P<item>.*?) Count: (?P<count>\d+) Location: X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)")

    # New Regexes
    # 2025.12.21-19.34.02: [LogExplosives] User: Player(123) Action: Armed Item: C4 Location: X=...
    REGEX_EXPLOSIVES = re.compile(r"(?P<timestamp>[\d\.-]+): \[LogExplosives\] User: (?P<name>.*?) \(\d+, (?P<steam_id>[\w:]+)\) Action: (?P<action>.*?) Item: (?P<item>.*?) Location: X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)")

    # 2025.12.23-06.01.36: [LogBunkerLock] C4 Bunker is Active. Activated ... X=...
    REGEX_BUNKER = re.compile(r"(?P<timestamp>[\d\.-]+): \[LogBunkerLock\] (?P<bunker>.*?) (?:is|Activated) (?P<status>Active|Locked|Activated).*?(?:X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+))?")

    @staticmethod
    def parse(line: str) -> Union[SentinelRaidMinigame, SentinelCrafting, SentinelExplosiveEvent, SentinelBunkerEvent, None]:
        line = line.strip()
        
        if "[LogMinigame]" in line:
            match = GameplayParserV2.REGEX_MINIGAME.search(line)
            if match:
                data = match.groupdict()
                return SentinelRaidMinigame(
                    timestamp=GameplayParserV2._ts(data["timestamp"]),
                    attacker_steam_id=extract_user_id(data["atk_id"]),
                    attacker_name=data["atk_name"],
                    target_owner_steam_id=extract_user_id(data.get("def_id")),
                    target_owner_name=data.get("def_name"),
                    minigame_class=data["minigame"],
                    target_object=data["target"],
                    lock_type=data.get("lock"),
                    is_success=(data["success"] == "Yes"),
                    failed_attempts=int(data["failed"]),
                    elapsed_time=float(data["time"]),
                    location={"x": float(data['x']), "y": float(data['y']), "z": float(data['z'])}
                )

        if "[LogCrafting]" in line:
            match_c = GameplayParserV2.REGEX_CRAFTING.search(line)
            if match_c:
                data = match_c.groupdict()
                return SentinelCrafting(
                    timestamp=GameplayParserV2._ts(data["timestamp"]),
                    crafter_steam_id=extract_user_id(data["steam_id"]),
                    crafter_name=data["name"],
                    item_class=data["item"],
                    count=int(data["count"]),
                    location={"x": float(data['x']), "y": float(data['y']), "z": float(data['z'])}
                )

        if "[LogExplosives]" in line:
            match_e = GameplayParserV2.REGEX_EXPLOSIVES.search(line)
            if match_e:
                data = match_e.groupdict()
                return SentinelExplosiveEvent(
                    timestamp=GameplayParserV2._ts(data["timestamp"]),
                    steam_id=extract_user_id(data["steam_id"]),
                    player_name=data["name"],
                    action=data["action"],
                    item_class=data["item"],
                    location={"x": float(data['x']), "y": float(data['y']), "z": float(data['z'])}
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
                    bunker_name=data["bunker"],
                    action=data["status"],
                    location=loc
                )
                
        return None

    @staticmethod
    def _ts(ts_str: str):
        try:
            return datetime.strptime(ts_str, "%Y.%m.%d-%H.%M.%S")
        except:
            return datetime.utcnow()
