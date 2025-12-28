"""
Script para criar índices nas tabelas de análise econômica
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def create_indexes():
    indexes = [
        # Player Wallets
        "CREATE INDEX IF NOT EXISTS idx_wallets_last_transaction ON sentinel_player_wallets(last_transaction)",
        "CREATE INDEX IF NOT EXISTS idx_wallets_player_name ON sentinel_player_wallets(player_name)",
        
        # Item Economy
        "CREATE INDEX IF NOT EXISTS idx_item_economy_class ON sentinel_item_economy(item_class)",
        "CREATE INDEX IF NOT EXISTS idx_item_economy_period ON sentinel_item_economy(period_start, period_end)",
        "CREATE INDEX IF NOT EXISTS idx_item_economy_demand ON sentinel_item_economy(demand_level)",
        
        # Economy Alerts
        "CREATE INDEX IF NOT EXISTS idx_alerts_type ON sentinel_economy_alerts(alert_type)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_severity ON sentinel_economy_alerts(severity)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_status ON sentinel_economy_alerts(status)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_steam_id ON sentinel_economy_alerts(steam_id)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_detected ON sentinel_economy_alerts(detected_at DESC)",
        
        # Trader Inventory
        "CREATE INDEX IF NOT EXISTS idx_trader_inv_name ON sentinel_trader_inventory(trader_name)",
        "CREATE INDEX IF NOT EXISTS idx_trader_inv_time ON sentinel_trader_inventory(snapshot_time DESC)",
        "CREATE INDEX IF NOT EXISTS idx_trader_inv_funds ON sentinel_trader_inventory(funds)",
        
        # Account Registry
        "CREATE INDEX IF NOT EXISTS idx_account_owner ON sentinel_account_registry(current_owner_steam_id)",
        "CREATE INDEX IF NOT EXISTS idx_account_active ON sentinel_account_registry(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_account_last_tx ON sentinel_account_registry(last_transaction DESC)",
    ]
    
    async with AsyncSession(engine) as session:
        print("🔧 Criando índices...\n")
        
        success = 0
        for idx, sql in enumerate(indexes, 1):
            try:
                await session.execute(text(sql))
                await session.commit()
                success += 1
                print(f"  ✅ [{idx}/{len(indexes)}] Índice criado")
            except Exception as e:
                await session.rollback()
                if "already exists" in str(e):
                    print(f"  ℹ️  [{idx}/{len(indexes)}] Índice já existe")
                else:
                    print(f"  ⚠️  [{idx}/{len(indexes)}] Erro: {str(e)[:60]}")
        
        print(f"\n✅ {success} índices criados com sucesso!")

if __name__ == "__main__":
    asyncio.run(create_indexes())
