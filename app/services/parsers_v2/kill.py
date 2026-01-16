import re
import json
import math
from datetime import datetime
from typing import Optional
from app.models.kill_v2 import SentinelKill
from app.services.parsers_v2.utils import extract_user_id

class KillParserV2:
    # 2025.12.21-19.18.27: {"Killer":{...}, ...}
    # REGEX para a linha de resumo (Died: ...) que contém a distância oficial
    # Ex: Died: Dark (7656...), Killer: Tsujiro (7656...) ... Distance: 27.02 m]
    # Atualizado para capturar IDs com possíveis prefixos
    REGEX_SUMMARY = re.compile(r"(?P<timestamp>[\d\.-]+): Died: .*Killer: .*\((?P<killer_id>[\w:]+)\).*Distance: (?P<distance>[\d\.]+) m")

    # REGEX para o JSON principal (padrão antigo e novo)
    REGEX_JSON = re.compile(r"(?P<timestamp>[\d\.-]+): (?P<json_data>\{.*\})")

    # Mémoria temporária para guardar o resumo da linha anterior
    _last_summary: Optional[dict] = None
    
    # ========================================================================
    # WEAPON CATEGORIZATION
    # ========================================================================
    WEAPON_CATEGORIES = {
        'Weapon_AKS_74U': 'Assault Rifle',
        'Weapon_AK47': 'Assault Rifle',
        'Weapon_AK74': 'Assault Rifle',
        'Weapon_M4A1': 'Assault Rifle',
        'Weapon_M16A4': 'Assault Rifle',
        'Weapon_AS_Val': 'Assault Rifle',
        'Weapon_SCAR': 'Assault Rifle',
        'Weapon_VHS2': 'Assault Rifle',
        'Weapon_MK18': 'Assault Rifle',
        'Weapon_M1_Garand': 'Assault Rifle',
        'Weapon_STG44': 'Assault Rifle',
        
        'Weapon_M249': 'LMG',
        'Weapon_RPK': 'LMG',
        'Weapon_MG42': 'LMG',
        'Weapon_M60': 'LMG',
        
        'Weapon_MP5': 'SMG',
        'Weapon_MAC10': 'SMG',
        'Weapon_UZI': 'SMG',
        'Weapon_TommyGun': 'SMG',
        'Weapon_UMP': 'SMG',
        'Weapon_MP40': 'SMG',
        'Weapon_PPSH': 'SMG',
        
        'Weapon_SVD': 'Sniper Rifle',
        'Weapon_MosinNagant': 'Sniper Rifle',
        'Weapon_M82A1': 'Sniper Rifle',
        'Weapon_VSS': 'Sniper Rifle',
        'Weapon_KAR98': 'Sniper Rifle',
        'Weapon_98k': 'Sniper Rifle',
        'Weapon_Hunter85': 'Sniper Rifle',
        'Weapon_AWM': 'Sniper Rifle',
        'Weapon_Afloat': 'Sniper Rifle',
        'Weapon_CarbonHunter': 'Sniper Rifle',
        'Weapon_M1891': 'Sniper Rifle',
        
        'Weapon_Glock': 'Pistol',
        'Weapon_DEagle': 'Pistol',
        'Weapon_M9': 'Pistol',
        'Weapon_CZ75': 'Pistol',
        'Weapon_Block21': 'Pistol',
        'Weapon_SF19': 'Pistol',
        'Weapon_HS9': 'Pistol',
        'Weapon_1911': 'Pistol',
        'Weapon_Judge': 'Pistol',
        'Weapon_PC9': 'Pistol',
        
        'Weapon_Shotgun': 'Shotgun',
        'Weapon_SPAS': 'Shotgun',
        'Weapon_DT11B': 'Shotgun',
        'Weapon_Tec01_490': 'Shotgun',
        'Weapon_M1887': 'Shotgun',
        
        'Bow': 'Archery',
        'Crossbow': 'Archery',
        
        '1H_': 'Melee',
        '2H_': 'Melee',
        'Knife': 'Melee',
        'Axe': 'Melee',
        'Machete': 'Melee',
        'Spear': 'Melee',
        'Sledgehammer': 'Melee',
        'Bat': 'Melee',
        'Crowbar': 'Melee',
        'Sword': 'Melee',
        
        'C4': 'Explosive',
        'Grenade': 'Explosive',
        'Mine': 'Explosive',
        'RPG': 'Explosive',
        'Claymore': 'Explosive',
        
        'Vehicle': 'Vehicle',
        'Car': 'Vehicle',
        'Heli': 'Vehicle',
        'Plane': 'Vehicle',
        'Boat': 'Vehicle',
        'BPC_': 'Vehicle',
    }
    
    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================
    
    @staticmethod
    def parse_weapon(weapon_str: str) -> tuple:
        """
        Parse weapon string into class, damage type, and category
        Ex: "Weapon_AKS_74U_C [Projectile]" -> ("Weapon_AKS_74U_C", "Projectile", "Assault Rifle")
        """
        if not weapon_str:
            return "Unknown", "Unknown", "Other"
        
        # Extract weapon class and damage type
        match = re.match(r'(.+?)\s*\[(.+?)\]', weapon_str)
        if match:
            weapon_class = match.group(1).strip()
            damage_type = match.group(2).strip()
        else:
            weapon_class = weapon_str
            damage_type = "Unknown"
        
        # Determine category
        weapon_category = KillParserV2._get_weapon_category(weapon_class)
        
        return weapon_class, damage_type, weapon_category
    
    @staticmethod
    def _get_weapon_category(weapon_class: str) -> str:
        """Get weapon category from weapon class"""
        for key, category in KillParserV2.WEAPON_CATEGORIES.items():
            if key in weapon_class:
                return category
        
        # Fallback detection
        if 'Fall' in weapon_class or 'Drown' in weapon_class:
            return 'Environment'
        if 'BP_' in weapon_class or 'Guard' in weapon_class:
            return 'NPC'
        
        return 'Other'
    
    @staticmethod
    def is_npc(name: str, user_id: str) -> tuple:
        """
        Detect if player is NPC and return (is_npc, npc_type)
        """
        if not name:
            return False, None
        
        npc_patterns = {
            'BP_Guard': 'Guard',
            'BP_Puppet': 'Puppet',
            'BP_Mech': 'Mech',
            'BP_Animal': 'Animal',
            'BP_Drifter': 'Drifter', # Drifters sao NPCs
            'BOT_': 'Bot',
        }
        
        for pattern, npc_type in npc_patterns.items():
            if pattern in name:
                return True, npc_type

        # Catch-all: Se começar com 'BP_' e não for um dos acima, ainda é provavelmente um NPC/Asset do jogo que matou alguem (ex: Mina)
        if name.startswith('BP_'):
             return True, 'Environment'
        
        # SteamID inválido também indica NPC ou Log de Erro
        if not user_id or len(str(user_id)) < 10:
            return True, 'Unknown'
            
        # Casos onde o ID é -1 (Suicídio por mina/ambiente as vezes vem assim)
        if str(user_id) == "-1":
             return True, 'Environment'
        
        return False, None
    
    @staticmethod
    def calculate_grid(location: dict, grid_size: int = 1000000) -> tuple:
        """
        Calculate grid coordinates for hotspot analysis
        Default grid size: 1,000,000 cm = 10km
        """
        if not location:
            return None, None
        
        try:
            x = float(location.get('X', 0))
            y = float(location.get('Y', 0))
            
            grid_x = int(x / grid_size)
            grid_y = int(y / grid_size)
            
            return grid_x, grid_y
        except:
            return None, None

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
                    "killer_id": extract_user_id(summary_match.group("killer_id")),
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
            
            # Extract IDs safely
            k_id = extract_user_id(killer.get("UserId"))
            v_id = extract_user_id(victim.get("UserId"))

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
                KillParserV2._last_summary.get("killer_id") == k_id):
                
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
            
            # --- NEW: Parse Weapon Details ---
            weapon_full = payload.get("Weapon", "Unknown")
            weapon_class, damage_type, weapon_category = KillParserV2.parse_weapon(weapon_full)
            
            # --- NEW: Detect NPCs ---
            killer_name = killer.get("ProfileName")
            victim_name = victim.get("ProfileName")
            
            killer_is_npc, killer_npc_type = KillParserV2.is_npc(killer_name, k_id)
            victim_is_npc, victim_npc_type = KillParserV2.is_npc(victim_name, v_id)
            
            # --- NEW: Calculate Grid ---
            grid_x, grid_y = KillParserV2.calculate_grid(s_loc)

            return SentinelKill(
                timestamp=KillParserV2._ts(ts_str),
                killer_id=k_id,
                killer_name=killer_name,
                killer_loc_server=s_loc,
                killer_loc_client=c_loc,
                killer_immortal=killer.get("HasImmortality", False),
                
                victim_id=v_id,
                victim_name=victim_name,
                victim_loc=victim.get("ServerLocation"),
                
                weapon=weapon_full,
                weapon_class=weapon_class,
                damage_type=damage_type,
                weapon_category=weapon_category,
                
                distance=final_distance,
                is_event=killer.get("IsInGameEvent", False),
                
                killer_is_npc=killer_is_npc,
                killer_npc_type=killer_npc_type,
                victim_is_npc=victim_is_npc,
                victim_npc_type=victim_npc_type,
                
                grid_x=grid_x,
                grid_y=grid_y,
                
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
