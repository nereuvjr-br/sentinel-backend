from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelAdminCommand(SQLModel, table=True):
    __tablename__ = "sentinel_admin_commands"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    # Executor Identity
    admin_steam_id: str = Field(index=True)
    admin_name: str
    admin_game_id: Optional[str] = None # As string purely for flexibility
    
    # Command Details
    raw_command: str = Field(description="O comando original completo")
    command_type: str = Field(index=True, description="Tipo normalizado: SpawnItem, Teleport, etc")
    
    # Context / Arguments (Extracted)
    target_steam_id: Optional[str] = None
    target_name: Optional[str] = None
    
    item_class: Optional[str] = None
    item_count: Optional[int] = None
    item_args: Optional[str] = None
    
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Metadata
    is_automated: bool = Field(default=False, index=True) # Flag para Bots
    processed_at: datetime = Field(default_factory=datetime.utcnow)
