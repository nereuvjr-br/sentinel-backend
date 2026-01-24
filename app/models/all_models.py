from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON
from decimal import Decimal

# Import notification model
from app.models.notification_v2 import SentinelNotificationLog

# --- CORE EVENTS ---

class LogChat(SQLModel, table=True):
    __tablename__ = "logs_chat"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    steam_id: Optional[str] = Field(default=None, index=True)
    player_name: Optional[str] = None
    game_id: Optional[int] = None
    channel: Optional[str] = None  # Global, Local, Squad
    message: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class LogKill(SQLModel, table=True):
    __tablename__ = "logs_kills"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    killer_id: Optional[str] = None
    killer_name: Optional[str] = None
    killer_loc: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    victim_id: Optional[str] = None
    victim_name: Optional[str] = None
    victim_loc: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    weapon: Optional[str] = None
    is_event: bool = Field(default=False)
    # New Anti-Cheat & Meta Fields
    client_loc: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    server_loc: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    distance_delta: Optional[float] = None
    is_immortal: Optional[bool] = None
    time_of_day: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class LogLogin(SQLModel, table=True):
    __tablename__ = "logs_login"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    steam_id: str
    player_name: Optional[str] = None
    game_id: Optional[int] = None
    ip_address: Optional[str] = None
    action: str  # login / logout
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    processed_at: datetime = Field(default_factory=datetime.utcnow)

# --- ADMINISTRATION & RULES ---

class LogViolation(SQLModel, table=True):
    __tablename__ = "logs_violations"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    steam_id: Optional[str] = None
    player_name: Optional[str] = None
    game_id: Optional[int] = None
    violation_type: str
    details: Optional[str] = None
    # New Anti-Cheat Fields
    suspicious_count: Optional[int] = None
    ban_count: Optional[int] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class LogAdmin(SQLModel, table=True):
    __tablename__ = "logs_admin"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    steam_id: Optional[str] = None
    player_name: Optional[str] = None
    game_id: Optional[int] = None
    command: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class LogEconomy(SQLModel, table=True):
    __tablename__ = "logs_economy"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    steam_id: Optional[str] = None
    player_name: Optional[str] = None
    type: str  # Bank / Trade
    account_number: Optional[str] = None
    amount: Optional[Decimal] = None
    details: Optional[str] = None
    # New Economy Intelligence Fields
    item_name: Optional[str] = None
    item_count: Optional[int] = None
    trader_name: Optional[str] = None
    balance_after: Optional[Decimal] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)

# --- EXTENDED EVENTS (V9.0) ---

class LogVehicle(SQLModel, table=True):
    __tablename__ = "logs_vehicle"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    vehicle_id: Optional[str] = None
    vehicle_name: Optional[str] = None
    reason: Optional[str] = None  # Destroyed / Expired
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class LogChest(SQLModel, table=True):
    __tablename__ = "logs_chest"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    entity_id: str
    action: str  # OwnershipChanged / Claimed
    old_owner_id: Optional[str] = None
    new_owner_id: Optional[str] = None
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class LogGameplay(SQLModel, table=True):
    __tablename__ = "logs_gameplay"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    event_type: str  # BunkerLock, etc
    event_name: Optional[str] = None
    location: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    # New Gameplay / Raid Radar Fields
    target_owner_id: Optional[str] = None
    target_owner_name: Optional[str] = None
    minigame_type: Optional[str] = None # Lockpick, Defuse
    is_success: Optional[bool] = None
    failed_attempts: Optional[int] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class LogFame(SQLModel, table=True):
    __tablename__ = "logs_fame"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    steam_id: Optional[str] = None
    player_name: Optional[str] = None
    amount: Optional[Decimal] = None
    reason: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)

# --- SYSTEM CONTROL ---

class ServiceOffset(SQLModel, table=True):
    """Controla até onde cada arquivo de log já foi lido para evitar duplicatas."""
    __tablename__ = "service_offsets"
    filename: str = Field(primary_key=True)
    last_read_offset: int = Field(default=0)
    last_modified: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
