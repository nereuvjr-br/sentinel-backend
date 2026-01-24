from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional, Dict, Any

class SentinelNotificationLog(SQLModel, table=True):
    """
    Registro de todas as notificações enviadas via WhatsApp.
    Rastreia sucesso, falhas, destinatários e conteúdo.
    """
    __tablename__ = "sentinel_notification_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Timestamp do envio
    sent_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Tipo de notificação (raid, kill, admin_alert, etc)
    notification_type: str = Field(index=True, max_length=50)
    
    # Destinatário
    recipient_phone: str = Field(index=True, max_length=100)  # Número ou Group JID
    recipient_type: str = Field(max_length=20)  # "player", "clan_group", "clan_member"
    recipient_steam_id: Optional[str] = Field(default=None, index=True, max_length=50)
    recipient_name: Optional[str] = Field(default=None, max_length=255)
    
    # Conteúdo da mensagem
    message_content: str = Field(sa_column=Column(JSON))  # Texto completo enviado
    
    # Contexto do evento que gerou a notificação
    event_context: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Status do envio
    status: str = Field(index=True, max_length=20)  # "success", "failed", "pending"
    
    # Detalhes de erro (se houver)
    error_message: Optional[str] = Field(default=None)
    
    # Response da API
    api_response_code: Optional[int] = Field(default=None)
    api_response_body: Optional[str] = Field(default=None)
    
    # Metadata adicional
    evolution_instance: Optional[str] = Field(default=None, max_length=100)
    retry_count: int = Field(default=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "notification_type": "raid_alert",
                "recipient_phone": "5577998094395",
                "recipient_type": "player",
                "recipient_steam_id": "76561198254469454",
                "recipient_name": "PlayerName",
                "message_content": "🚨 ALARME DE BASE...",
                "status": "success",
                "api_response_code": 201
            }
        }
