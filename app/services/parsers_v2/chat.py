import re
from datetime import datetime
from typing import Optional
from app.models.chat_v2 import SentinelChatMessage

from app.services.parsers_v2.utils import extract_user_id

class ChatParserV2:
    # 2025.12.21-16.08.25: '76561199817469068:BOT_Oblivion(21)' 'Global: O pacote AKS74 foi dropado no Warzone!'
    # Group 1: Timestamp
    # Group 2: SteamID
    # Group 3: Name
    # Group 4: GameID
    # Group 5: Channel
    # Group 6: Message
    REGEX_CHAT = re.compile(r"(?P<timestamp>[\d\.-]+): '(?P<steam_id>[\w:]+):(?P<name>.*?)\((?P<game_id>\d+)\)' '(?P<channel>.*?): (?P<message>.*)'")

    @staticmethod
    def parse(line: str) -> Optional[SentinelChatMessage]:
        line = line.strip()
        match = ChatParserV2.REGEX_CHAT.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        
        # Detect Automation
        name_upper = data["name"].upper()
        # Se for BOT ou se o nome for apenas NUMEROS (às vezes acontece em bug logs)
        is_auto = "BOT" in name_upper
        
        return SentinelChatMessage(
            timestamp=ChatParserV2._ts(data["timestamp"]),
            steam_id=extract_user_id(data["steam_id"]),
            player_name=data["name"],
            game_id=int(data["game_id"]),
            channel=data["channel"],
            message=data["message"],
            is_automated=is_auto
        )

    @staticmethod
    def _ts(ts_str: str):
        from datetime import timezone
        try:
            # SCUM logs are naturally UTC
            dt = datetime.strptime(ts_str, "%Y.%m.%d-%H.%M.%S")
            return dt.replace(tzinfo=timezone.utc)
        except:
            return datetime.now(timezone.utc)
