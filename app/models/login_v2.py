from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelLogin(SQLModel, table=True):
    __tablename__ = "sentinel_logins"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    # Identity
    steam_id: str = Field(index=True)
    player_name: str
    game_id: Optional[int] = None
    ip_address: str = Field(index=True, description="IPv4 Address used for connection")
    
    # Event Details
    action: str = Field(index=True) # "Login" or "Logout"
    login_type: str = Field(default="Standard", description="Standard or Drone")
    
    # Geolocation
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)
