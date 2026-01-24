from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelNotificationQueue(SQLModel, table=True):
    """
    Fila de Notificações para envio diferido (Delay da versão Free).
    """
    __tablename__ = "sentinel_notification_queue"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    recipient_phone: str = Field(index=True, max_length=100)
    message_content: str = Field()
    
    # Quando enviar
    scheduled_for: datetime = Field(index=True)
    
    # Status: pending, processed, failed
    status: str = Field(default="pending", index=True, max_length=20)
    
    # Metadados opcionais (para contexto)
    event_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
