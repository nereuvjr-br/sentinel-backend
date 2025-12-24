from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

async def wipe():
    print("⚠️ INICIANDO WIPE TOTAL DOS DADOS SENTINEL V2...")
    
    tables = [
        "sentinel_admin_commands",
        "sentinel_chat_messages",
        "sentinel_logins",
        "sentinel_kills",
        "sentinel_economy_trades",
        "sentinel_economy_balances",
        "sentinel_gameplay_raids",
        "sentinel_gameplay_crafting",
        "sentinel_gameplay_explosives",
        "sentinel_gameplay_bunkers",
        "sentinel_violations",
        "sentinel_chest_events",
        "sentinel_fame_events",
        "sentinel_bank_transactions",
        "sentinel_mechanic_services",
        "sentinel_bank_cards",
        "sentinel_unparsed_logs",
        "sentinel_processed_files" # Clean tracking to force re-ingestion
    ]
    
    async with AsyncSession(engine) as session:
        for table in tables:
            try:
                # CASCADE is needed if there are FKs, though V2 uses mostly independent logs.
                await session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                print(f"🗑️  Truncated {table}")
            except Exception as e:
                print(f"❌ Failed to truncate {table}: {e}")
        
        await session.commit()
    
    print("✨ Wipe Completo. O banco está limpo e pronto para re-ingestão pós-Wipe.")

if __name__ == "__main__":
    asyncio.run(wipe())
