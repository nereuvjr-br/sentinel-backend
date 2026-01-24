from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON

class SentinelClan(SQLModel, table=True):
    """Tabela de Clãs extraída do SCUM.db"""
    __tablename__ = "sentinel_clans"

    id: Optional[int] = Field(default=None, primary_key=True)
    scum_clan_id: int = Field(index=True, unique=True) # ID interno do jogo
    name: str = Field(index=True)
    leader_steam_id: Optional[str] = Field(default=None, index=True)
    description: Optional[str] = None
    whatsapp_group_id: Optional[str] = None
    
    member_count: int = Field(default=0, index=True)
    
    created_at: Optional[datetime] = None
    
    # Subscription & Plan
    plan_tier: str = Field(default="free", max_length=20)
    plan_expires_at: Optional[datetime] = Field(default=None)
    notification_settings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SentinelClanMember(SQLModel, table=True):
    """Membros do Clã com Rank"""
    __tablename__ = "sentinel_clan_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    clan_id: int = Field(foreign_key="sentinel_clans.scum_clan_id", index=True)
    steam_id: str = Field(index=True) # Player Steam ID
    
    rank: str = Field(default="Member") # Leader, Officer, Member
    
    joined_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
