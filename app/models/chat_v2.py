from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class SentinelChatMessage(SQLModel, table=True):
    __tablename__ = "sentinel_chat_messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    # Author Identity
    steam_id: str = Field(index=True)
    player_name: str
    game_id: Optional[int] = None
    
    # Message Integers
    channel: str = Field(index=True) # Global, Local, Squad, Admin
    message: str = Field(index=True) # Indexed for rudimentary search
    
    # Classification
    is_automated: bool = Field(default=False, index=True) # True for BOTs
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)
