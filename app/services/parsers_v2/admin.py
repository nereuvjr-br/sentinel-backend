import re
from datetime import datetime
from typing import Optional
from app.models.admin_v2 import SentinelAdminCommand

from app.services.parsers_v2.utils import extract_user_id

class AdminParserV2:
    # 1. Base Log Pattern
    # 2025.12.21-18.06.15: '76561199817469068:BOT_Oblivion(21)' Command: 'teleport 0 0 0'
    # Updated to capture raw id
    REGEX_BASE = re.compile(r"(?P<timestamp>[\d\.-]+): '(?P<steam_id>[\w:]+):(?P<name>.*?)\((?P<game_id>\d+)\)' Command: '(?P<command>.*)'")
    
    # 2. Map Teleport Pattern (Specific Variation)
    REGEX_MAP_TP = re.compile(r"(?P<timestamp>[\d\.-]+): '(?P<steam_id>[\w:]+):(?P<name>.*?)\((?P<game_id>\d+)\)' Used map click teleport to player: '(?P<target_raw>.*)' Location: X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)")

    # 3. Argument Extractors (Inside Command String)
    # SpawnItem Weapon_MK18 1 Location "-409464.75 ... 37995.668" AmmoCount 30
    REGEX_ARGS_SPAWN = re.compile(r"(?i)SpawnItem\s+(?P<item>[\w_]+)\s+(?P<count>\d+)\s+Location\s+\"(?P<loc_str>[^\"]+)\"(?:\s+(?P<extra>.*))?")

    @staticmethod
    def parse(line: str) -> Optional[SentinelAdminCommand]:
        line = line.strip()
        if not line: return None
        
        # Ignora lixo de sistema
        if "Game version:" in line or "Deleting players" in line or "Completed in" in line:
            return None

        # -- TENTA TELEPORTE DE MAPA (PRIORIDADE) --
        match_tp = AdminParserV2.REGEX_MAP_TP.search(line)
        if match_tp:
            data = match_tp.groupdict()
            return SentinelAdminCommand(
                timestamp=AdminParserV2._ts(data["timestamp"]),
                admin_steam_id=extract_user_id(data["steam_id"]),
                admin_name=data["name"],
                admin_game_id=data["game_id"],
                raw_command=f"MapTeleport > {data['target_raw']}",
                command_type="MapTeleport",
                target_name=data['target_raw'].split(':')[1] if ':' in data['target_raw'] else data['target_raw'],
                location={"x": float(data['x']), "y": float(data['y']), "z": float(data['z'])},
                is_automated=("BOT" in data["name"].upper())
            )

        # -- TENTA COMANDO PADRÃO --
        match = AdminParserV2.REGEX_BASE.search(line)
        if not match:
            return None
            
        data = match.groupdict()
        cmd_full = data["command"].strip()
        cmd_keys = cmd_full.split(' ')
        cmd_type = cmd_keys[0] if cmd_keys else "Unknown"
        
        # Detecta Automação
        is_bot = "BOT" in data["name"].upper()
        
        # Prepara objeto base
        model = SentinelAdminCommand(
            timestamp=AdminParserV2._ts(data["timestamp"]),
            admin_steam_id=extract_user_id(data["steam_id"]),
            admin_name=data["name"],
            admin_game_id=data["game_id"],
            raw_command=cmd_full,
            command_type=cmd_type,
            is_automated=is_bot
        )
        
        # -- ENRICHMENT: SPAWN ITEM --
        if "SpawnItem" in cmd_type: # Case insensitive check done via logic or proper normalization
            match_spawn = AdminParserV2.REGEX_ARGS_SPAWN.search(cmd_full)
            if match_spawn:
                s_data = match_spawn.groupdict()
                model.item_class = s_data["item"]
                model.item_count = int(s_data["count"])
                model.item_args = s_data.get("extra")
                
                # Parse Location String "-409464.75 -9808.166 37995.668"
                try:
                    coords = s_data["loc_str"].split()
                    if len(coords) >= 3:
                        model.location = {
                            "x": float(coords[0]),
                            "y": float(coords[1]), 
                            "z": float(coords[2])
                        }
                except:
                    pass

        return model

    @staticmethod
    def _ts(ts_str: str):
        try:
            return datetime.strptime(ts_str, "%Y.%m.%d-%H.%M.%S")
        except:
            return datetime.utcnow()
