import asyncio
import logging
from sqlalchemy import text
from app.core.database import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def optimize_database():
    logger.info("Starting database optimization...")
    
    async with engine.begin() as conn:
        logger.info("Adding index to sentinel_clans.member_count...")
        # Check if index exists to avoid error, or just catch it. 
        # Postgres 'IF NOT EXISTS' is handy.
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sentinel_clans_member_count ON sentinel_clans (member_count)"))
        
        logger.info("Adding index to sentinel_players_registry.last_seen if not exists...")
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sentinel_players_registry_last_seen ON sentinel_players_registry (last_seen)"))
        
        # Analyze tables to update statistics for the query planner
        logger.info("Analyzing tables...")
        await conn.execute(text("ANALYZE sentinel_clans"))
        await conn.execute(text("ANALYZE sentinel_players_registry"))
        
    logger.info("Optimization complete.")

if __name__ == "__main__":
    asyncio.run(optimize_database())
