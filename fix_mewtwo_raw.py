
import asyncio
import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Direct DB connection string from config hopefully or hardcoded for this script if needed
# But better to use the app's engine if possible, but the previous one failed.
# I will try to use the app's engine but with a raw execution.

from app.core.database import engine

async def fix_mewtwo_raw():
    async with engine.begin() as conn:
        print("--- Updating ADM_Mewtwo to Premium + 30 Days (Raw SQL) ---")
        
        # Calculate date
        expire_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
        
        stmt = text("""
            UPDATE sentinel_players_registry 
            SET plan_tier = 'premium', plan_expires_at = :dt 
            WHERE current_name = 'ADM_Mewtwo'
        """)
        
        await conn.execute(stmt, {"dt": expire_date})
        print("✅ Executed update successfully.")

if __name__ == "__main__":
    asyncio.run(fix_mewtwo_raw())
