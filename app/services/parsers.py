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
