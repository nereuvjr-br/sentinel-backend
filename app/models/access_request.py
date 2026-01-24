from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class SentinelAccessRequest(SQLModel, table=True):
    """Solicitações de acesso ao sistema de notificações"""
    __tablename__ = "sentinel_access_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    steam_id: str = Field(index=True, max_length=255)
    phone_number: str = Field(max_length=50)
    player_name: str = Field(max_length=255) # Nome informado pelo user para facilitar
    
    status: str = Field(default="PENDING", index=True) # PENDING, APPROVED, REJECTED
    
    ip_address: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    
    rejection_reason: Optional[str] = None
