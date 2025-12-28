from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import TIMESTAMP

class SentinelParserMetrics(SQLModel, table=True):
    """
    Métricas detalhadas de performance e saúde de cada parser.
    Atualizado a cada ciclo de processamento.
    """
    __tablename__ = "sentinel_parser_metrics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    parser_name: str = Field(index=True)  # Admin, Chat, Login, Kill, Economy, etc.
    
    # Contadores de Processamento
    total_lines_processed: int = Field(default=0)
    total_lines_success: int = Field(default=0)
    total_lines_failed: int = Field(default=0)
    total_unparsed: int = Field(default=0)
    
    # Performance
    avg_parse_time_ms: float = Field(default=0.0)  # Tempo médio de parse por linha
    last_batch_size: int = Field(default=0)
    last_batch_time_ms: float = Field(default=0.0)
    
    # Status de Saúde
    success_rate: float = Field(default=100.0)  # Percentual de sucesso
    is_healthy: bool = Field(default=True)
    last_error: Optional[str] = None
    error_count_last_hour: int = Field(default=0)
    
    # Timestamps
    last_processed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=False))
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=False))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=False))
    )


class SentinelDatabaseHealth(SQLModel, table=True):
    """
    Snapshot do estado de saúde do banco de dados.
    Registra contagens de registros por tabela e detecta anomalias.
    """
    __tablename__ = "sentinel_database_health"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Contadores por Tabela (Core)
    count_admin_commands: int = Field(default=0)
    count_chat_messages: int = Field(default=0)
    count_logins: int = Field(default=0)
    count_kills: int = Field(default=0)
    
    # Contadores Economia
    count_economy_trades: int = Field(default=0)
    count_economy_balances: int = Field(default=0)
    count_bank_transactions: int = Field(default=0)
    count_mechanic_services: int = Field(default=0)
    count_bank_cards: int = Field(default=0)
    
    # Contadores Gameplay
    count_raids: int = Field(default=0)
    count_crafting: int = Field(default=0)
    count_chest_events: int = Field(default=0)
    count_fame_events: int = Field(default=0)
    
    # Contadores Sistema
    count_violations: int = Field(default=0)
    count_vehicles: int = Field(default=0)
    count_unparsed_logs: int = Field(default=0)
    count_processed_files: int = Field(default=0)
    
    # Análise Agregada
    count_player_wallets: int = Field(default=0)
    count_item_economy: int = Field(default=0)
    count_economy_alerts: int = Field(default=0)
    count_trader_inventory: int = Field(default=0)
    count_account_registry: int = Field(default=0)
    
    # Taxas de Crescimento (últimos 5 minutos)
    growth_rate_kills: float = Field(default=0.0)
    growth_rate_trades: float = Field(default=0.0)
    growth_rate_logins: float = Field(default=0.0)
    
    # Status Geral
    is_healthy: bool = Field(default=True)
    health_issues: Optional[str] = Field(default=None, sa_column=Column(JSON))
    
    # Timestamp
    snapshot_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=False))
    )


class SentinelIngestionLog(SQLModel, table=True):
    """
    Log detalhado de cada ciclo de ingestão.
    Permite rastrear exatamente o que foi processado e quando.
    """
    __tablename__ = "sentinel_ingestion_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Identificação
    filename: str = Field(index=True)
    log_type: str = Field(index=True)  # Admin, Chat, Economy, etc.
    
    # Detalhes do Processamento
    bytes_processed: int = Field(default=0)
    lines_processed: int = Field(default=0)
    lines_success: int = Field(default=0)
    lines_failed: int = Field(default=0)
    
    # Performance
    processing_time_ms: float = Field(default=0.0)
    throughput_lines_per_sec: float = Field(default=0.0)
    
    # Resultado
    status: str = Field(default="success")  # success, partial, failed
    error_message: Optional[str] = None
    
    # Offset Tracking
    offset_start: int = Field(default=0)
    offset_end: int = Field(default=0)
    
    # Timestamp
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=False))
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=False))
    )


class SentinelSystemAlert(SQLModel, table=True):
    """
    Sistema de alertas para anomalias detectadas no monitoramento.
    """
    __tablename__ = "sentinel_system_alerts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Classificação
    alert_type: str = Field(index=True)  # parser_failure, db_anomaly, ingestion_stalled, etc.
    severity: str = Field(index=True)  # low, medium, high, critical
    
    # Detalhes
    component: str  # Nome do parser ou componente afetado
    title: str
    description: str
    evidence: Optional[str] = Field(default=None, sa_column=Column(JSON))
    
    # Status
    status: str = Field(default="open")  # open, acknowledged, resolved, false_positive
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    # Timestamps
    detected_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=False))
    )
    acknowledged_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=False))
    )
    resolved_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=False))
    )
