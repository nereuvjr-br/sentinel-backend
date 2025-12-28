import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def check_economy_tables():
    async with AsyncSession(engine) as session:
        tables = [
            'sentinel_player_wallets',
            'sentinel_item_economy',
            'sentinel_economy_alerts',
            'sentinel_trader_inventory',
            'sentinel_account_registry',
            'sentinel_admin_economy_actions'
        ]
        
        print("📊 Verificando tabelas de economia analítica...\n")
        
        for table in tables:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            
            if count > 0:
                print(f"✅ {table:40} : {count:6} registros")
            else:
                print(f"❌ {table:40} : {count:6} registros (VAZIO)")

asyncio.run(check_economy_tables())
