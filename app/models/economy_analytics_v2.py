from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON

class SentinelPlayerWallet(SQLModel, table=True):
    """Consolidação do estado atual da carteira de cada jogador"""
    __tablename__ = "sentinel_player_wallets"
    
    steam_id: str = Field(primary_key=True, max_length=255)
    player_name: str = Field(max_length=255)
    
    # Saldos Atuais
    cash: float = Field(default=0.0)
    bank: float = Field(default=0.0)
    gold: float = Field(default=0.0)
    
    # Metadados Financeiros
    total_earned: float = Field(default=0.0)
    total_spent: float = Field(default=0.0)
    
    # Contas Bancárias
    primary_account_number: Optional[str] = Field(default=None, max_length=50)
    account_count: int = Field(default=0)
    
    # Timestamps
    first_seen: datetime
    last_transaction: datetime
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SentinelItemEconomy(SQLModel, table=True):
    """Análise agregada da economia de cada item"""
    __tablename__ = "sentinel_item_economy"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    item_class: str = Field(max_length=255, index=True)
    
    # Estatísticas de Compra
    total_purchases: int = Field(default=0)
    total_purchase_value: float = Field(default=0.0)
    avg_purchase_price: Optional[float] = None
    
    # Estatísticas de Venda
    total_sales: int = Field(default=0)
    total_sale_value: float = Field(default=0.0)
    avg_sale_price: Optional[float] = None
    avg_sale_health: Optional[float] = None  # Durabilidade média
    avg_sale_uses: Optional[int] = None      # Munição/cargas médias
    
    # Análise de Mercado
    price_trend: Optional[str] = Field(default=None, max_length=20)  # rising, falling, stable
    demand_level: Optional[str] = Field(default=None, max_length=20) # high, medium, low
    
    # Traders
    most_sold_trader: Optional[str] = Field(default=None, max_length=255)
    most_bought_trader: Optional[str] = Field(default=None, max_length=255)
    
    # Período de Análise
    period_start: datetime
    period_end: datetime
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SentinelEconomyAlert(SQLModel, table=True):
    """Sistema de alertas automáticos para anomalias econômicas"""
    __tablename__ = "sentinel_economy_alerts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    alert_type: str = Field(max_length=50, index=True)  # dupe_detected, inflation_spike, etc
    severity: str = Field(max_length=20, index=True)     # low, medium, high, critical
    
    # Contexto
    steam_id: Optional[str] = Field(default=None, max_length=255, index=True)
    player_name: Optional[str] = Field(default=None, max_length=255)
    trader_name: Optional[str] = Field(default=None, max_length=255)
    item_class: Optional[str] = Field(default=None, max_length=255)
    account_number: Optional[str] = Field(default=None, max_length=50)
    
    # Detalhes
    description: str
    evidence: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Status
    status: str = Field(default="open", max_length=20)  # open, investigating, resolved, false_positive
    assigned_admin: Optional[str] = Field(default=None, max_length=255)
    
    # Timestamps
    detected_at: datetime = Field(index=True)
    resolved_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SentinelTraderInventory(SQLModel, table=True):
    """Rastreamento de estoque e fundos de traders"""
    __tablename__ = "sentinel_trader_inventory"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    trader_name: str = Field(max_length=255, index=True)
    
    # Estado Financeiro
    funds: float
    
    # Estoque
    item_class: Optional[str] = Field(default=None, max_length=255)
    stock_quantity: Optional[int] = None
    
    # Contexto
    users_online: Optional[int] = None
    
    # Timestamp
    snapshot_time: datetime = Field(index=True)


class SentinelAccountRegistry(SQLModel, table=True):
    """Registro de todas as contas bancárias"""
    __tablename__ = "sentinel_account_registry"
    
    account_number: str = Field(primary_key=True, max_length=50)
    
    # Proprietário Atual
    current_owner_steam_id: str = Field(max_length=255, index=True)
    current_owner_name: str = Field(max_length=255)
    
    # Histórico
    created_at: datetime
    last_transaction: Optional[datetime] = None
    
    # Estatísticas
    total_deposits: float = Field(default=0.0)
    total_withdrawals: float = Field(default=0.0)
    total_transfers_in: float = Field(default=0.0)
    total_transfers_out: float = Field(default=0.0)
    
    # Flags
    is_active: bool = Field(default=True)
    has_card: bool = Field(default=False)
    card_type: Optional[str] = Field(default=None, max_length=100)
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
