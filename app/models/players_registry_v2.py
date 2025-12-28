from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import ARRAY, String

class SentinelPlayerRegistry(SQLModel, table=True):
    """Registro central de jogadores com histórico de nomes e squads"""
    __tablename__ = "sentinel_players_registry"
    
    steam_id: str = Field(primary_key=True, max_length=255)
    
    # Nome Atual
    current_name: str = Field(max_length=255, index=True)
    previous_names: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    
    # Squad/Clã
    squad_name: Optional[str] = Field(default=None, max_length=255, index=True)
    squad_tag: Optional[str] = Field(default=None, max_length=50, index=True)
    squad_joined_at: Optional[datetime] = None
    
    # Estatísticas Básicas
    first_seen: datetime = Field(index=True)
    last_seen: datetime = Field(index=True)
    total_logins: int = Field(default=0)
    total_playtime_hours: float = Field(default=0.0)
    
    # Flags
    is_active: bool = Field(default=True, index=True)
    is_banned: bool = Field(default=False)
    is_admin: bool = Field(default=False)
    
    # Metadados
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SentinelNameChange(SQLModel, table=True):
    """Histórico de mudanças de nome"""
    __tablename__ = "sentinel_name_changes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    steam_id: str = Field(max_length=255, index=True, foreign_key="sentinel_players_registry.steam_id")
    
    old_name: Optional[str] = Field(default=None, max_length=255)
    new_name: str = Field(max_length=255)
    
    changed_at: datetime = Field(index=True)
    detected_in: str = Field(max_length=50)  # login, chat, kill, economy, etc
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
