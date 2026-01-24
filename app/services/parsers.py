import re
import json
from datetime import datetime
from typing import Optional, Union, Dict, Any
from sqlmodel import SQLModel  # <--- FIXED IMPORT
from app.models.all_models import (
    LogChat, LogKill, LogLogin, LogViolation, 
    LogAdmin, LogEconomy, LogVehicle, LogChest, 
    LogGameplay, LogFame
)

class LogParser:
    # Compilando Regex para performance (baseado no README V9.2)
    
    # 2025.12.21-19.17.54
    TIMESTAMP_FMT = "%Y.%m.%d-%H.%M.%S"
    
    # Regex Patterns
    # Regex Patterns
    REGEX_CHAT = re.compile(r"(?P<timestamp>[\d\.-]+): '(?P<steam_id>\d+):(?P<name>.*?)\((?P<game_id>\d+)\)' '(?P<channel>.*?): (?P<message>.*)'")
    
    # Kill Feed: JSON based
    REGEX_KILL_JSON = re.compile(r"(?P<timestamp>[\d\.-]+): (?P<json_data>\{.*\})")
    
    REGEX_LOGIN = re.compile(r"(?P<timestamp>[\d\.-]+): '(?P<ip>[\d\.]+) (?P<steam_id>\d+):(?P<name>.*?)\((?P<game_id>\d+)\)' logged (?P<action>in|out) at: (?:X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)|\?)")
    
    # Violation: Captures Counts
    REGEX_VIOLATION = re.compile(r"(?P<timestamp>[\d\.-]+): \[(?P<type>.*?)\] (?P<details>.*?),.*Count: \d+, SuspiciousCount: (?P<suspicious>\d+), BanCount: (?P<ban>\d+), User: (?P<name>.*?) \((?P<game_id>\d+), (?P<steam_id>\d+)\)")
    
    REGEX_ADMIN = re.compile(r"(?P<timestamp>[\d\.-]+): '(?P<steam_id>\d+):(?P<name>.*?)\((?P<game_id>\d+)\)' Command: '(?P<command>.*)'")
    REGEX_ADMIN_TELEPORT = re.compile(r"(?P<timestamp>[\d\.-]+): '(?P<steam_id>\d+):(?P<name>.*?)\((?P<game_id>\d+)\)' Used map click teleport to player: '(?P<target>.*)' Location: (?P<loc>.*)")
    
    # ... (Economy Regexes remain here) ...

    @staticmethod
    def _parse_admin(line: str) -> Optional[LogAdmin]:
        # Tenta Comando Padrão
        match = LogParser.REGEX_ADMIN.search(line)
        if match:
            data = match.groupdict()
            return LogAdmin(
                timestamp=LogParser.parse_timestamp(data["timestamp"]),
                steam_id=data["steam_id"],
                player_name=data["name"],
                game_id=int(data["game_id"]),
                command=data["command"]
            )
            
        # Tenta Teleporte via Mapa
        match_tp = LogParser.REGEX_ADMIN_TELEPORT.search(line)
        if match_tp:
            data = match_tp.groupdict()
            return LogAdmin(
                timestamp=LogParser.parse_timestamp(data["timestamp"]),
                steam_id=data["steam_id"],
                player_name=data["name"],
                game_id=int(data["game_id"]),
                command=f"MapTeleport to {data['target']} at {data['loc']}"
            )
            
        return None

    @staticmethod
    def _parse_economy(line: str) -> Optional[LogEconomy]:
        # Tenta match Genérico para timestamp e tipo
        match_gen = LogParser.REGEX_ECONOMY_GENERIC.search(line)
        if not match_gen:
            return None
            
        data_gen = match_gen.groupdict()
        ts = LogParser.parse_timestamp(data_gen["timestamp"])
        eco_type = data_gen["type"]
        details = data_gen["details"]
        
        # Objeto base
        model = LogEconomy(
            timestamp=ts,
            type=eco_type,
            details=details
        )
        
        # Enrichment based on sub-regexes
        if "Trade" in eco_type:
            match_trade = LogParser.REGEX_ECONOMY_TRADE.search(line)
            if match_trade:
                trade_data = match_trade.groupdict()
                model.item_name = trade_data["item_name"]
                model.trader_name = trade_data["trader"]
                model.balance_after = float(trade_data["balance"])
                model.steam_id = trade_data["steam_id"]
                model.player_name = trade_data["buyer_name"]
                # Default count 1 se não extraído
                model.item_count = 1 
        
        elif "Bank" in eco_type:
            match_bank = LogParser.REGEX_ECONOMY_BANK.search(line)
            if match_bank:
                bank_data = match_bank.groupdict()
                model.steam_id = bank_data["steam_id"]
                model.player_name = bank_data["name"]
                model.balance_after = float(bank_data["balance"])
                
        return model

    @staticmethod
    def _parse_vehicle(line: str) -> Optional[LogVehicle]:
        match = LogParser.REGEX_VEHICLE.search(line)
        if not match:
            return None
        data = match.groupdict()
        
        loc = None
        if data.get("x"):
            loc = {"x": data["x"], "y": data["y"], "z": data["z"]}
            
        return LogVehicle(
            timestamp=LogParser.parse_timestamp(data["timestamp"]),
            reason=data["reason"],
            vehicle_name=data["vehicle_name"],
            vehicle_id=data["vehicle_id"],
            owner_id=data.get("owner_id"), # Pode ser None
            owner_name=data.get("owner_name"),
            location=loc
        )

    @staticmethod
    def _parse_chest(line: str) -> Optional[LogChest]:
        # Implementação simplificada para chest ownership
        if "ownership" not in line: return None
        
        # Tenta usar a regex genérica
        # TODO: Aprimorar para diferenciar Old/New owner no caso de TROCA
        parts = line.split(" ")
        # Fallback manual simples se regex falhar, ou avançar depois
        return None # Placeholder seguro por enquanto para nao quebrar

    @staticmethod
    def _parse_gameplay(line: str) -> Optional[LogGameplay]:
        # 1. Bunker Lock
        if "LogBunkerLock" in line:
            match = LogParser.REGEX_GAMEPLAY_BUNKER.search(line)
            if match:
                data = match.groupdict()
                return LogGameplay(
                    timestamp=LogParser.parse_timestamp(data["timestamp"]),
                    event_type="BunkerLock",
                    event_name=f"{data['bunker_name']} Active",
                    location={"x": float(data["x"]), "y": float(data["y"]), "z": float(data["z"])}
                )

        # 2. Minigames (Lockpick / Defuse) -> Raid Radar
        if "LogMinigame" in line:
            match = LogParser.REGEX_GAMEPLAY_MINIGAME.search(line)
            if match:
                data = match.groupdict()
                return LogGameplay(
                    timestamp=LogParser.parse_timestamp(data["timestamp"]),
                    event_type="RaidMinigame",
                    event_name=data["minigame"], # LockpickingMinigame_C etc
                    target_owner_id=data["target_owner_id"],
                    minigame_type=data["minigame"].replace("Minigame_C", ""),
                    is_success=(data["success"] == "Yes"),
                    failed_attempts=int(data["failed"])
                )

        # 3. Crafting
        if "LogCrafting" in line:
            match = LogParser.REGEX_GAMEPLAY_CRAFTING.search(line)
            if match:
                data = match.groupdict()
                return LogGameplay(
                    timestamp=LogParser.parse_timestamp(data["timestamp"]),
                    event_type="Crafting",
                    event_name=f"Crafted {data['item']} x{data['count']}",
                    location={"x": float(data["x"]), "y": float(data["y"]), "z": float(data["z"])}
                )
        
        return None

    @staticmethod
    def _parse_fame(line: str) -> Optional[LogFame]:
        match = LogParser.REGEX_FAME.search(line)
        if not match:
            return None
        data = match.groupdict()
        return LogFame(
            timestamp=LogParser.parse_timestamp(data["timestamp"]),
            player_name=data["player_name"],
            steam_id=data["steam_id"],
            amount=float(data["amount"]),
            reason=data["reason"]
        )

    @staticmethod
    def parse_timestamp(ts_str: str) -> datetime:
        try:
            return datetime.strptime(ts_str, LogParser.TIMESTAMP_FMT)
        except:
            return datetime.utcnow()

    @staticmethod
    def process_line(filename: str, line: str) -> Optional[SQLModel]:
        line = line.strip()
        if not line: return None
        
        fname = filename.lower()
        
        if "login" in fname:
            return LogParser._parse_login(line)
        elif "admin" in fname:
            return LogParser._parse_admin(line)
        elif "economy" in fname:
            return LogParser._parse_economy(line)
        elif "kill" in fname:
            return LogParser._parse_kill(line)
        elif "chat" in fname:
            return LogParser._parse_chat(line)
        elif "violation" in fname:
            return LogParser._parse_violation(line)
        elif "gameplay" in fname:
            return LogParser._parse_gameplay(line)
        elif "vehicle" in fname:
            return LogParser._parse_vehicle(line)
        elif "chest" in fname:
            return LogParser._parse_chest(line)
        elif "fame" in fname:
            return LogParser._parse_fame(line)
            
        return None

    @staticmethod
    def _parse_login(line: str) -> Optional[LogLogin]:
        match = LogParser.REGEX_LOGIN.search(line)
        if not match: return None
        
        data = match.groupdict()
        l_type = "Standard"
        if "(as drone)" in line: l_type = "Drone"
        
        loc = None
        if data.get('x'):
             loc = {"x": float(data['x']), "y": float(data['y']), "z": float(data['z'])}

        return LogLogin(
             timestamp=LogParser.parse_timestamp(data["timestamp"]),
             ip_address=data["ip"],
             steam_id=data["steam_id"],
             player_name=data["name"],
             game_id=int(data["game_id"]),
             action=data["action"].title(), 
             login_type=l_type,
             location=loc
        )

    @staticmethod
    def _parse_kill(line: str) -> Optional[LogKill]:
        match = LogParser.REGEX_KILL_JSON.search(line)
        if not match: return None
        
        try:
            data = match.groupdict()
            json_str = data["json_data"]
            # Fix Common JSON Scum Weirdness if any (usually ok in simplified logs)
            obj = json.loads(json_str)
            
            # Extract info from JSON
            # Structure usually: {"Killer": {...}, "Victim": {...}, "Weapon": "..."}
            # We map to LogKill model
            
            killer = obj.get("Killer", {})
            victim = obj.get("Victim", {})
            
            return LogKill(
                timestamp=LogParser.parse_timestamp(data["timestamp"]),
                killer_name=killer.get("Name"),
                killer_id=killer.get("UserId"),
                killer_loc={"x": killer.get("ServerLocation", {}).get("X"), "y": killer.get("ServerLocation", {}).get("Y"), "z": killer.get("ServerLocation", {}).get("Z")},
                victim_name=victim.get("Name"),
                victim_id=victim.get("UserId"),
                victim_loc={"x": victim.get("ServerLocation", {}).get("X"), "y": victim.get("ServerLocation", {}).get("Y"), "z": victim.get("ServerLocation", {}).get("Z")},
                weapon=obj.get("Weapon", "Unknown"),
                distance=float(obj.get("KillDistance", 0.0)),
                is_event=obj.get("InGameEvent", False)
            )
        except:
            return None

    @staticmethod
    def _parse_chat(line: str) -> Optional[LogChat]:
        match = LogParser.REGEX_CHAT.search(line)
        if not match: return None
        data = match.groupdict()
        
        return LogChat(
            timestamp=LogParser.parse_timestamp(data["timestamp"]),
            steam_id=data["steam_id"],
            player_name=data["name"],
            game_id=int(data["game_id"]),
            channel=data["channel"].strip(),
            message=data["message"]
        )

    @staticmethod
    def _parse_violation(line: str) -> Optional[LogViolation]:
        match = LogParser.REGEX_VIOLATION.search(line)
        if not match: return None
        data = match.groupdict()
        
        return LogViolation(
            timestamp=LogParser.parse_timestamp(data["timestamp"]),
            type=data["type"],
            details=data["details"],
            suspicious_count=int(data["suspicious"]),
            ban_count=int(data["ban"]),
            player_name=data["name"],
            game_id=int(data["game_id"]),
            steam_id=data["steam_id"]
        )
