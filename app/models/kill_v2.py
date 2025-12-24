from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelKill(SQLModel, table=True):
    __tablename__ = "sentinel_kills"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    # Killer
    killer_id: Optional[str] = Field(index=True) # Pode ser nulo (Suicídio/Ambiente)
    killer_name: Optional[str]
    killer_loc_server: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    killer_loc_client: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    killer_immortal: bool = Field(default=False)
    
    # Victim
    victim_id: str = Field(index=True)
    victim_name: str
    victim_loc: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # The Deal
    weapon: str = Field(index=True)
    distance: float = Field(default=0.0)
    is_event: bool = Field(default=False)
    
    # Environmental / Anti-Cheat
    time_of_day: Optional[str] = None
    violation_score: float = Field(default=0.0) # Delta Server/Client distance
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)
