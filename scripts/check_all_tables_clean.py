
import asyncio
import logging
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

# Silenciar logs do SQLAlchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

async def check_all_tables():
    tables = [
        'sentinel_kills',
        'sentinel_logins',
        'sentinel_chat_messages',
        'sentinel_economy_trades',
        'sentinel_economy_balances',
        'sentinel_bank_transactions',
        'sentinel_mechanic_services',
        'sentinel_bank_cards',
        'sentinel_admin_commands',
        'sentinel_gameplay_raids',
        'sentinel_gameplay_crafting',
        'sentinel_gameplay_explosives',
        'sentinel_gameplay_bunkers',
        'sentinel_chest_events',
        'sentinel_fame_events',
        'sentinel_violations',
        'sentinel_vehicles',
        'sentinel_player_wallets',
        'sentinel_item_economy',
        'sentinel_economy_alerts',
        'sentinel_trader_inventory',
        'sentinel_account_registry',
        'sentinel_admin_economy_actions',
        'sentinel_players_registry',
        'sentinel_name_changes',
        'sentinel_processed_files',
        'sentinel_unparsed_logs'
    ]
    
    print(f"{'TABELA':<35} | {'REGISTROS':<10}")
    print("-" * 50)
    
    async with AsyncSession(engine) as session:
        for table in tables:
            try:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                status = "✅ OK" if count > 0 else "⚠️  VAZIA"
                print(f"{table:<35} | {count:<10} {status}")
            except Exception as e:
                print(f"{table:<35} | ERRO: {e}")

if __name__ == "__main__":
    asyncio.run(check_all_tables())
