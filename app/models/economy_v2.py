from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON, Text

# ============================================================================
# TRADES - Compras e Vendas de Itens
# ============================================================================
class SentinelEconomyTrade(SQLModel, table=True):
    __tablename__ = "sentinel_economy_trades"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    steam_id: str = Field(index=True)
    player_name: str
    account_number: Optional[str] = None  # Número da conta bancária interna do SCUM
    
    # Trade Details
    trade_type: str = Field(index=True) # "Purchase" (Buy from Trader) or "Sell" (Sell to Trader)
    item_class: str = Field(index=True)
    item_count: int = Field(default=1)
    
    # Item Condition (Captura completa de durabilidade e usos)
    item_health: Optional[float] = None  # Durabilidade do item (0-100)
    item_uses: Optional[int] = None      # Usos/munição restantes
    
    total_price: float
    trader_name: str
    
    # Service Flag
    is_mechanic_service: bool = Field(default=False)  # True se for serviço de mecânico
    
    # Market State
    users_online: Optional[int] = None # "effective users online" - influences dynamic prices
    store_stock_before: Optional[int] = None
    store_stock_after: Optional[int] = None
    
    # Location (Coordenadas da transação)
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    pos_z: Optional[float] = None


# ============================================================================
# BALANCES - Snapshots de Saldo
# ============================================================================
class SentinelEconomyBalance(SQLModel, table=True):
    __tablename__ = "sentinel_economy_balances"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    steam_id: str = Field(index=True)
    player_name: str
    account_number: Optional[str] = None  # Número da conta bancária interna
    
    # Context
    trigger_event: str # "Before", "After"
    trader_name: Optional[str] = None
    
    # Wallet State
    cash: float
    bank: float
    gold: float
    
    # Trader State (If available)
    trader_funds: Optional[float] = None
    
    # Location
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    pos_z: Optional[float] = None
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# BANK TRANSACTIONS - Saques, Depósitos e Transferências
# ============================================================================
class SentinelBankTransaction(SQLModel, table=True):
    __tablename__ = "sentinel_bank_transactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    steam_id: str = Field(index=True)
    player_name: str
    account_number: str = Field(index=True)  # Conta de origem
    
    # Transaction Type
    transaction_type: str = Field(index=True)  # "deposit", "withdraw", "transfer"
    
    # Amounts
    gross_amount: float  # Valor bruto da transação
    net_amount: float    # Valor líquido (após taxas)
    fee: Optional[float] = None  # Taxa cobrada (gross - net)
    
    # Transfer Details (se for transferência)
    target_account: Optional[str] = None
    target_name: Optional[str] = None
    target_steam_id: Optional[str] = None
    
    # Location
    pos_x: float
    pos_y: float
    pos_z: float


# ============================================================================
# MECHANIC SERVICES - Serviços de Mecânico
# ============================================================================
class SentinelMechanicService(SQLModel, table=True):
    __tablename__ = "sentinel_mechanic_services"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    steam_id: str = Field(index=True)
    player_name: str
    
    # Service Details
    service_type: str = Field(index=True)  # "Buy", "Install", "Repair", "Remove"
    item_class: str = Field(index=True)    # Peça/attachment
    price: float
    trader_name: str
    
    # Location
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    pos_z: Optional[float] = None


# ============================================================================
# BANK CARD MANAGEMENT - Gestão de Cartões Bancários
# ============================================================================
class SentinelBankCard(SQLModel, table=True):
    __tablename__ = "sentinel_bank_cards"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    
    steam_id: str = Field(index=True)
    player_name: str
    account_number: str = Field(index=True)
    
    # Card Details
    action: str = Field(index=True)  # "purchased", "manually destroyed"
    card_type: str = Field(index=True)  # "Starter card", "Gold card", "Classic card"
    
    # Purchase Details (se aplicável)
    free_renewal: Optional[bool] = None
    new_balance: Optional[float] = None
    
    # Destruction Details (se aplicável)
    destroyed_account: Optional[str] = None  # Conta do cartão destruído
    
    # Location
    pos_x: float
    pos_y: float
    pos_z: float


# ============================================================================
# UNPARSED LOGS - Logs Não Reconhecidos (Anti-Fuga)
# ============================================================================
class SentinelUnparsedLog(SQLModel, table=True):
    __tablename__ = "sentinel_unparsed_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    log_type: str = Field(index=True)  # "economy", "kill", etc.
    filename: str
    raw_line: str = Field(sa_column=Column(Text))  # Linha completa não parseada
    
    # Metadata
    attempted_parsers: Optional[str] = None  # Lista de parsers que tentaram processar
    error_message: Optional[str] = None
