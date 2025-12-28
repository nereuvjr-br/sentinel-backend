import asyncio
import logging
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_wipe")
# Ensure we see SQL errors
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

async def wipe_database():
    logger.warning("⚠️ STARTING ROBUST DATABASE WIPE ⚠️")
    
    tables = [
        "sentinel_kills",
        "sentinel_logins",
        "sentinel_chat_messages",
        "sentinel_admin_commands",
        "sentinel_economy_trades",
        "sentinel_economy_balances",
        "sentinel_bank_transactions",
        "sentinel_mechanic_services",
        "sentinel_bank_cards",
        "sentinel_gameplay_raids",      # Fixed name
        "sentinel_gameplay_crafting",   # Fixed name
        "sentinel_gameplay_explosives", # Fixed name
        "sentinel_gameplay_bunkers",    # Fixed name
        "sentinel_chest_events",
        "sentinel_fame_events",
        "sentinel_violations",
        "sentinel_unparsed_logs",
        "sentinel_processed_files",
        "sentinel_player_wallets",
        "sentinel_item_economy",
        "sentinel_name_changes",
        "sentinel_vehicles",
        "sentinel_players_registry"
    ]
    
    async with AsyncSession(engine) as session:
        for table in tables:
            try:
                # Use individual transactions for isolation
                async with session.begin(): # Starts transaction, commits on exit
                    # CASCADE is important if foreign keys exist
                    await session.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
                logger.info(f"✅ Truncated {table}")
            except Exception as e:
                logger.error(f"❌ Failed to truncate {table}: {e}")
        
    logger.info("✨ Database Wipe Attempt Completed. ✨")

if __name__ == "__main__":
    asyncio.run(wipe_database())
