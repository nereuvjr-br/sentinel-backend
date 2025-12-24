import re
import json
import math
from datetime import datetime
from typing import Optional
from app.models.kill_v2 import SentinelKill

class KillParserV2:
    # 2025.12.21-19.18.27: {"Killer":{...}, ...}
    # REGEX para a linha de resumo (Died: ...) que contém a distância oficial
    # Ex: Died: Dark (7656...), Killer: Tsujiro (7656...) ... Distance: 27.02 m]
    REGEX_SUMMARY = re.compile(r"(?P<timestamp>[\d\.-]+): Died: .*Killer: .*\((?P<killer_id>\d+)\).*Distance: (?P<distance>[\d\.]+) m")

    # REGEX para o JSON principal (padrão antigo e novo)
    REGEX_JSON = re.compile(r"(?P<timestamp>[\d\.-]+): (?P<json_data>\{.*\})")

    # Mémoria temporária para guardar o resumo da linha anterior
    _last_summary: Optional[dict] = None

    @staticmethod
    def parse(line: str) -> Optional[SentinelKill]:
        line = line.strip()
        
        # 1. Tenta capturar a linha de Resumo (Died) para pegar a distância oficial
        summary_match = KillParserV2.REGEX_SUMMARY.search(line)
        if summary_match:
            try:
                # Store distance with timestamp key to ensure we match the right kill later
                KillParserV2._last_summary = {
                    "timestamp": summary_match.group("timestamp"),
                    "killer_id": summary_match.group("killer_id"),
                    "distance": float(summary_match.group("distance"))
                }
            except:
                pass
            return None # Não salvamos nada ainda, esperamos o JSON

        # 2. Se não for resumo, tenta ser a linha JSON principal
        if "{" not in line: return None
        
        match = KillParserV2.REGEX_JSON.search(line)
        if not match: return None
        
        try:
            ts_str = match.group("timestamp")
            payload = json.loads(match.group("json_data"))
            
            killer = payload.get("Killer", {}) or {}
            victim = payload.get("Victim", {}) or {}
            
            # --- Anti-Cheat Calculation (Violation Score) ---
            s_loc = killer.get("ServerLocation")
            c_loc = killer.get("ClientLocation")
            score = 0.0
            
            if s_loc and c_loc:
                try:
                    dx = s_loc.get('X', 0) - c_loc.get('X', 0)
                    dy = s_loc.get('Y', 0) - c_loc.get('Y', 0)
                    dz = s_loc.get('Z', 0) - c_loc.get('Z', 0)
                    score = math.sqrt(dx*dx + dy*dy + dz*dz) / 100.0
                except:
                    pass

            # --- Official Distance Handling ---
            final_distance = 0.0
            
            # Tenta usar a distância oficial capturada na linha anterior
            if (KillParserV2._last_summary and 
                KillParserV2._last_summary.get("timestamp") == ts_str and
                KillParserV2._last_summary.get("killer_id") == killer.get("UserId")):
                
                final_distance = KillParserV2._last_summary["distance"]
                # Limpa a memória após uso
                KillParserV2._last_summary = None
            else:
                # Fallback: Calcula matematicamente se não tiver resumo
                try:
                    k_pos = s_loc
                    v_pos = victim.get("ServerLocation")
                    if k_pos and v_pos:
                         dx = k_pos.get('X', 0) - v_pos.get('X', 0)
                         dy = k_pos.get('Y', 0) - v_pos.get('Y', 0)
                         dz = k_pos.get('Z', 0) - v_pos.get('Z', 0)
                         final_distance = math.sqrt(dx*dx + dy*dy + dz*dz) / 100.0
                except:
                    pass

            return SentinelKill(
                timestamp=KillParserV2._ts(ts_str),
                killer_id=killer.get("UserId"),
                killer_name=killer.get("ProfileName"),
                killer_loc_server=s_loc,
                killer_loc_client=c_loc,
                killer_immortal=killer.get("HasImmortality", False),
                
                victim_id=victim.get("UserId"),
                victim_name=victim.get("ProfileName"),
                victim_loc=victim.get("ServerLocation"),
                
                weapon=payload.get("Weapon", "Unknown"),
                distance=final_distance,
                is_event=killer.get("IsInGameEvent", False),
                
                time_of_day=payload.get("TimeOfDay"),
                violation_score=score
            )
        except:
            return None

    @staticmethod
    def _ts(ts_str: str):
        from datetime import timezone
        
        try:
            # ParseSCUM format
            dt = datetime.strptime(ts_str, "%Y.%m.%d-%H.%M.%S")
            
            # SCUM Logs are always UTC based on observation
            # We force UTC here so that when it is displayed in Frontend (BRT),
            # the offset is applied correctly (e.g. 01:00 UTC -> 22:00 BRT).
            dt = dt.replace(tzinfo=timezone.utc)
            
            return dt
        except:
            return datetime.now(timezone.utc)
