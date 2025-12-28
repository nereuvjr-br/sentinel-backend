from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelAdminEconomyAction(SQLModel, table=True):
    """Rastreamento de comandos admin com impacto econômico"""
    __tablename__ = "sentinel_admin_economy_actions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    # Admin Info
    admin_steam_id: str = Field(max_length=255, index=True)
    admin_name: str = Field(max_length=255)
    admin_game_id: Optional[str] = Field(default=None, max_length=50)
    
    # Action Details
    action_type: str = Field(max_length=50, index=True)  # spawn_item, spawn_cash, destroy_item
    raw_command: str
    
    # Economic Impact
    item_class: Optional[str] = Field(default=None, max_length=255, index=True)
    item_quantity: Optional[int] = None
    stack_count: Optional[int] = None
    economic_value: Optional[float] = None  # Valor estimado em dinheiro
    
    # Target (se houver)
    target_steam_id: Optional[str] = Field(default=None, max_length=255)
    target_name: Optional[str] = Field(default=None, max_length=255)
    
    # Location
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Impact Classification
    impact_level: Optional[str] = Field(default=None, max_length=20, index=True)  # critical, high, medium, low
    is_cash_spawn: bool = Field(default=False, index=True)
    is_weapon_spawn: bool = Field(default=False)
    
    # Metadata
    is_automated: bool = Field(default=False)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
