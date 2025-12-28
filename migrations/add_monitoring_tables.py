"""
Migração: Adicionar Tabelas de Monitoramento
Data: 2025-12-26
Descrição: Cria tabelas para rastreamento de métricas de parsers, saúde do banco,
           logs de ingestão e alertas do sistema.
"""

from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio


async def upgrade():
    """Criar tabelas de monitoramento"""
    
    async with AsyncSession(engine) as session:
        # 1. Tabela de Métricas de Parser
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS sentinel_parser_metrics (
                id SERIAL PRIMARY KEY,
                parser_name VARCHAR(50) NOT NULL,
                
                total_lines_processed BIGINT DEFAULT 0,
                total_lines_success BIGINT DEFAULT 0,
                total_lines_failed BIGINT DEFAULT 0,
                total_unparsed BIGINT DEFAULT 0,
                
                avg_parse_time_ms DOUBLE PRECISION DEFAULT 0.0,
                last_batch_size INTEGER DEFAULT 0,
                last_batch_time_ms DOUBLE PRECISION DEFAULT 0.0,
                
                success_rate DOUBLE PRECISION DEFAULT 100.0,
                is_healthy BOOLEAN DEFAULT TRUE,
                last_error TEXT,
                error_count_last_hour INTEGER DEFAULT 0,
                
                last_processed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_parser_metrics_name 
                ON sentinel_parser_metrics(parser_name)
        """))
        
        # 2. Tabela de Saúde do Banco de Dados
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS sentinel_database_health (
                id SERIAL PRIMARY KEY,
                
                count_admin_commands BIGINT DEFAULT 0,
                count_chat_messages BIGINT DEFAULT 0,
                count_logins BIGINT DEFAULT 0,
                count_kills BIGINT DEFAULT 0,
                
                count_economy_trades BIGINT DEFAULT 0,
                count_economy_balances BIGINT DEFAULT 0,
                count_bank_transactions BIGINT DEFAULT 0,
                count_mechanic_services BIGINT DEFAULT 0,
                count_bank_cards BIGINT DEFAULT 0,
                
                count_raids BIGINT DEFAULT 0,
                count_crafting BIGINT DEFAULT 0,
                count_chest_events BIGINT DEFAULT 0,
                count_fame_events BIGINT DEFAULT 0,
                
                count_violations BIGINT DEFAULT 0,
                count_vehicles BIGINT DEFAULT 0,
                count_unparsed_logs BIGINT DEFAULT 0,
                count_processed_files BIGINT DEFAULT 0,
                
                count_player_wallets BIGINT DEFAULT 0,
                count_item_economy BIGINT DEFAULT 0,
                count_economy_alerts BIGINT DEFAULT 0,
                count_trader_inventory BIGINT DEFAULT 0,
                count_account_registry BIGINT DEFAULT 0,
                
                growth_rate_kills DOUBLE PRECISION DEFAULT 0.0,
                growth_rate_trades DOUBLE PRECISION DEFAULT 0.0,
                growth_rate_logins DOUBLE PRECISION DEFAULT 0.0,
                
                is_healthy BOOLEAN DEFAULT TRUE,
                health_issues JSONB,
                
                snapshot_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_db_health_snapshot 
                ON sentinel_database_health(snapshot_at DESC)
        """))
        
        # 3. Tabela de Logs de Ingestão
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS sentinel_ingestion_logs (
                id SERIAL PRIMARY KEY,
                
                filename VARCHAR(255) NOT NULL,
                log_type VARCHAR(50) NOT NULL,
                
                bytes_processed BIGINT DEFAULT 0,
                lines_processed INTEGER DEFAULT 0,
                lines_success INTEGER DEFAULT 0,
                lines_failed INTEGER DEFAULT 0,
                
                processing_time_ms DOUBLE PRECISION DEFAULT 0.0,
                throughput_lines_per_sec DOUBLE PRECISION DEFAULT 0.0,
                
                status VARCHAR(20) DEFAULT 'success',
                error_message TEXT,
                
                offset_start BIGINT DEFAULT 0,
                offset_end BIGINT DEFAULT 0,
                
                started_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP
            )
        """))
        
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ingestion_filename 
                ON sentinel_ingestion_logs(filename)
        """))
        
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ingestion_type 
                ON sentinel_ingestion_logs(log_type)
        """))
        
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ingestion_started 
                ON sentinel_ingestion_logs(started_at DESC)
        """))
        
        # 4. Tabela de Alertas do Sistema
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS sentinel_system_alerts (
                id SERIAL PRIMARY KEY,
                
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                
                component VARCHAR(100) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                evidence JSONB,
                
                status VARCHAR(20) DEFAULT 'open',
                acknowledged_by VARCHAR(100),
                resolved_by VARCHAR(100),
                resolution_notes TEXT,
                
                detected_at TIMESTAMP DEFAULT NOW(),
                acknowledged_at TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """))
        
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_alerts_type 
                ON sentinel_system_alerts(alert_type)
        """))
        
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_alerts_severity 
                ON sentinel_system_alerts(severity)
        """))
        
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_alerts_status 
                ON sentinel_system_alerts(status)
        """))
        
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_alerts_detected 
                ON sentinel_system_alerts(detected_at DESC)
        """))
        
        await session.commit()
        print("✅ Tabelas de monitoramento criadas com sucesso!")


async def downgrade():
    """Remover tabelas de monitoramento"""
    
    async with AsyncSession(engine) as session:
        await session.execute(text("DROP TABLE IF EXISTS sentinel_system_alerts CASCADE;"))
        await session.execute(text("DROP TABLE IF EXISTS sentinel_ingestion_logs CASCADE;"))
        await session.execute(text("DROP TABLE IF EXISTS sentinel_database_health CASCADE;"))
        await session.execute(text("DROP TABLE IF EXISTS sentinel_parser_metrics CASCADE;"))
        
        await session.commit()
        print("✅ Tabelas de monitoramento removidas com sucesso!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
