
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://admin:da139c45ed91909b2856206092736e80@159.65.174.208:5432/sentinel_dev"

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    
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
        'sentinel_trader_inventory',
        'sentinel_processed_files',
        'sentinel_unparsed_logs'
    ]

    print(f"\n{'TABELA':<35} | COUNT")
    print("-" * 45)

    async with engine.connect() as conn:
        for t in tables:
            try:
                res = await conn.execute(text(f"SELECT COUNT(*) FROM {t}"))
                print(f"{t:<35} | {res.scalar()}")
            except Exception as e:
                print(f"{t:<35} | ERROR: {e}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
