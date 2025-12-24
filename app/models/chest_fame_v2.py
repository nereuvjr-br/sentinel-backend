from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelChestEvent(SQLModel, table=True):
    __tablename__ = "sentinel_chest_events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    # Who did it?
    steam_id: str = Field(index=True) # New owner usually
    
    # What happened?
    action: str = Field(index=True) # "Claimed", "OwnershipChanged"
    entity_id: str = Field(index=True) # Unique Chest ID
    
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class SentinelFameEvent(SQLModel, table=True):
    __tablename__ = "sentinel_fame_events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    steam_id: str = Field(index=True)
    player_name: str
    
    amount: float
    reason: str = Field(index=True)
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)
