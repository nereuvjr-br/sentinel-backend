from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelRaidMinigame(SQLModel, table=True):
    __tablename__ = "sentinel_gameplay_raids"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    attacker_steam_id: str = Field(index=True)
    attacker_name: str
    target_owner_steam_id: Optional[str] = Field(index=True)
    target_owner_name: Optional[str] = None
    minigame_class: str = Field(index=True)
    target_object: str 
    lock_type: Optional[str] = None
    is_success: bool = Field(index=True)
    failed_attempts: int
    elapsed_time: float
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class SentinelCrafting(SQLModel, table=True):
    __tablename__ = "sentinel_gameplay_crafting"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    crafter_steam_id: str = Field(index=True)
    crafter_name: str
    item_class: str = Field(index=True)
    count: int = Field(default=1)
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class SentinelExplosiveEvent(SQLModel, table=True):
    __tablename__ = "sentinel_gameplay_explosives"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    steam_id: str = Field(index=True)
    player_name: str
    
    action: str = Field(index=True) # Armed, Disarmed
    item_class: str # BP_C4_...
    
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class SentinelBunkerEvent(SQLModel, table=True):
    __tablename__ = "sentinel_gameplay_bunkers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    bunker_name: str = Field(index=True) # "C4 Bunker", "A1 Bunker"
    action: str = Field(index=True) # "Active", "Activated", "Locked"
    
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    processed_at: datetime = Field(default_factory=datetime.utcnow)
