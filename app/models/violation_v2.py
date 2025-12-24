from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelViolation(SQLModel, table=True):
    __tablename__ = "sentinel_violations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    steam_id: str = Field(index=True)
    player_name: Optional[str] = None
    
    # Violation Type
    violation_class: str = Field(index=True) # "AmmoCountMismatch", "NetErrorUnauthorized"
    description: str # "Ammo count violation detected..." or "KickPlayer..."
    
    # Specifics (If Cheat)
    weapon: Optional[str] = None
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Offender History (Snapshot from log)
    suspicious_count: Optional[int] = 0
    ban_count: Optional[int] = 0
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)
