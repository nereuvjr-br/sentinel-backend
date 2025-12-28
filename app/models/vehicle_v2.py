from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelVehicle(SQLModel, table=True):
    __tablename__ = "sentinel_vehicles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    # Vehicle Identity
    vehicle_id: str = Field(index=True)      # Database ID (e.g. 1024)
    vehicle_class: str = Field(index=True)   # Class Name (e.g. BPC_Laika)
    
    # Event
    event_type: str  # Spawned, Destroyed, OwnershipChanged
    
    # Context
    owner_id: Optional[str] = Field(default=None, index=True)
    owner_name: Optional[str] = None
    
    # Location
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)
