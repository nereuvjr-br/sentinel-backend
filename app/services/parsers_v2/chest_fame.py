import re
from datetime import datetime
from typing import Optional, Union
from app.models.chest_fame_v2 import SentinelChestEvent, SentinelFameEvent

from app.services.parsers_v2.utils import extract_user_id

class ChestFameParserV2:
    # 1. CHEST
    # 2025.12.21-16.03.35: Chest (entity id: 1069) ownership claimed by 76561198414035288. Location: X=-67061.641 Y=-871545.625 Z=1477.723
    REGEX_CHEST = re.compile(r"(?P<timestamp>[\d\.-]+): Chest \(entity id: (?P<eid>\d+)\) ownership (?:(?P<action>claimed)\. Owner|(?P<action_chg>changed).*?New owner): (?P<steam_id>[\w:]+).*Location: X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)")
    
    # 2. FAME
    # 2025.12.21-16.10.51: Player BOT_Oblivion(76561199817469068) was awarded 20.000000 fame points for Kill.
    REGEX_FAME = re.compile(r"(?P<timestamp>[\d\.-]+): Player (?P<name>.*?)\((?P<steam_id>[\w:]+)\) was awarded (?P<amount>[\d\.-]+) fame points for (?P<reason>.*)")

    @staticmethod
    def parse_chest(line: str) -> Optional[SentinelChestEvent]:
        line = line.strip()
        match = ChestFameParserV2.REGEX_CHEST.search(line)
        if match:
            data = match.groupdict()
            return SentinelChestEvent(
                timestamp=ChestFameParserV2._ts(data["timestamp"]),
                steam_id=extract_user_id(data["steam_id"]),
                action=data.get("action") or data.get("action_chg") or "unknown",
                entity_id=data["eid"],
                location={"x": float(data['x']), "y": float(data['y']), "z": float(data['z'])}
            )
        return None

    @staticmethod
    def parse_fame(line: str) -> Optional[SentinelFameEvent]:
        line = line.strip()
        match = ChestFameParserV2.REGEX_FAME.search(line)
        if match:
            data = match.groupdict()
            return SentinelFameEvent(
                timestamp=ChestFameParserV2._ts(data["timestamp"]),
                steam_id=extract_user_id(data["steam_id"]),
                player_name=data["name"],
                amount=float(data["amount"]),
                reason=data["reason"].strip().rstrip('.')
            )
        return None

    @staticmethod
    def _ts(ts_str: str):
        try:
            return datetime.strptime(ts_str, "%Y.%m.%d-%H.%M.%S")
        except:
            return datetime.utcnow()
