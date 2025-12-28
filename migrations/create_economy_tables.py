"""
Script robusto para criar tabelas de análise econômica
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def create_tables():
    tables = [
        # 1. Player Wallets
        """
        CREATE TABLE IF NOT EXISTS sentinel_player_wallets (
            steam_id VARCHAR(255) PRIMARY KEY,
            player_name VARCHAR(255) NOT NULL,
            cash DOUBLE PRECISION DEFAULT 0,
            bank DOUBLE PRECISION DEFAULT 0,
            gold DOUBLE PRECISION DEFAULT 0,
            total_earned DOUBLE PRECISION DEFAULT 0,
            total_spent DOUBLE PRECISION DEFAULT 0,
            primary_account_number VARCHAR(50),
            account_count INTEGER DEFAULT 0,
            first_seen TIMESTAMP NOT NULL,
            last_transaction TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # 2. Item Economy
        """
        CREATE TABLE IF NOT EXISTS sentinel_item_economy (
            id SERIAL PRIMARY KEY,
            item_class VARCHAR(255) NOT NULL,
            total_purchases BIGINT DEFAULT 0,
            total_purchase_value DOUBLE PRECISION DEFAULT 0,
            avg_purchase_price DOUBLE PRECISION,
            total_sales BIGINT DEFAULT 0,
            total_sale_value DOUBLE PRECISION DEFAULT 0,
            avg_sale_price DOUBLE PRECISION,
            avg_sale_health DOUBLE PRECISION,
            avg_sale_uses INTEGER,
            price_trend VARCHAR(20),
            demand_level VARCHAR(20),
            most_sold_trader VARCHAR(255),
            most_bought_trader VARCHAR(255),
            period_start TIMESTAMP NOT NULL,
            period_end TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(item_class, period_start)
        )
        """,
        
        # 3. Economy Alerts
        """
        CREATE TABLE IF NOT EXISTS sentinel_economy_alerts (
            id SERIAL PRIMARY KEY,
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            steam_id VARCHAR(255),
            player_name VARCHAR(255),
            trader_name VARCHAR(255),
            item_class VARCHAR(255),
            account_number VARCHAR(50),
            description TEXT NOT NULL,
            evidence JSONB,
            status VARCHAR(20) DEFAULT 'open',
            assigned_admin VARCHAR(255),
            detected_at TIMESTAMP NOT NULL,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # 4. Trader Inventory
        """
        CREATE TABLE IF NOT EXISTS sentinel_trader_inventory (
            id SERIAL PRIMARY KEY,
            trader_name VARCHAR(255) NOT NULL,
            funds DOUBLE PRECISION NOT NULL,
            item_class VARCHAR(255),
            stock_quantity INTEGER,
            users_online INTEGER,
            snapshot_time TIMESTAMP NOT NULL,
            UNIQUE(trader_name, item_class, snapshot_time)
        )
        """,
        
        # 5. Account Registry
        """
        CREATE TABLE IF NOT EXISTS sentinel_account_registry (
            account_number VARCHAR(50) PRIMARY KEY,
            current_owner_steam_id VARCHAR(255) NOT NULL,
            current_owner_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL,
            last_transaction TIMESTAMP,
            total_deposits DOUBLE PRECISION DEFAULT 0,
            total_withdrawals DOUBLE PRECISION DEFAULT 0,
            total_transfers_in DOUBLE PRECISION DEFAULT 0,
            total_transfers_out DOUBLE PRECISION DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            has_card BOOLEAN DEFAULT FALSE,
            card_type VARCHAR(100),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    table_names = [
        "sentinel_player_wallets",
        "sentinel_item_economy",
        "sentinel_economy_alerts",
        "sentinel_trader_inventory",
        "sentinel_account_registry"
    ]
    
    async with AsyncSession(engine) as session:
        print("🚀 Criando tabelas de análise econômica...\n")
        
        for idx, (sql, name) in enumerate(zip(tables, table_names), 1):
            try:
                await session.execute(text(sql))
                await session.commit()
                print(f"  ✅ [{idx}/5] {name}")
            except Exception as e:
                await session.rollback()
                if "already exists" in str(e):
                    print(f"  ℹ️  [{idx}/5] {name} (já existe)")
                else:
                    print(f"  ❌ [{idx}/5] {name} - Erro: {str(e)[:80]}")
        
        print("\n✅ Processo concluído!")

if __name__ == "__main__":
    asyncio.run(create_tables())
