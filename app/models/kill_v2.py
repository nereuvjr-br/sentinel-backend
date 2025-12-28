from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelKill(SQLModel, table=True):
    __tablename__ = "sentinel_kills"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    # Killer
    killer_id: Optional[str] = Field(default=None, index=True) # Pode ser nulo (Suicídio/Ambiente)
    killer_name: Optional[str] = None
    killer_loc_server: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    killer_loc_client: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    killer_immortal: bool = Field(default=False)
    
    # Victim
    victim_id: str = Field(index=True)
    victim_name: str
    victim_loc: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Weapon Details (NEW)
    weapon: str = Field(index=True)  # Full weapon string (legacy)
    weapon_class: Optional[str] = Field(default=None, max_length=255, index=True)
    damage_type: Optional[str] = Field(default=None, max_length=50, index=True)
    weapon_category: Optional[str] = Field(default=None, max_length=50, index=True)
    
    # Kill Details
    distance: float = Field(default=0.0)
    is_event: bool = Field(default=False)
    
    # NPC Detection (NEW)
    killer_is_npc: bool = Field(default=False, index=True)
    killer_npc_type: Optional[str] = Field(default=None, max_length=50)
    victim_is_npc: bool = Field(default=False, index=True)
    victim_npc_type: Optional[str] = Field(default=None, max_length=50)
    
    # Advanced Features (NEW)
    is_revenge_kill: bool = Field(default=False)
    revenge_for_kill_id: Optional[int] = None
    kill_streak_id: Optional[int] = None
    
    # Hotspots (NEW)
    grid_x: Optional[int] = None
    grid_y: Optional[int] = None
    
    # Environmental / Anti-Cheat
    time_of_day: Optional[str] = None
    violation_score: float = Field(default=0.0) # Delta Server/Client distance
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)

