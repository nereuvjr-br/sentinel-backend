
import asyncio
from datetime import datetime, timedelta
from app.core.database import engine
from sqlalchemy import text

async def fix_mewtwo_naive():
    async with engine.begin() as conn:
        print("--- Updating ADM_Mewtwo to Premium + 30 Days (Naive) ---")
        
        # Use naive UTC time
        expire_date = datetime.utcnow() + timedelta(days=30)
        
        stmt = text("""
            UPDATE sentinel_players_registry 
            SET plan_tier = 'premium', plan_expires_at = :dt 
            WHERE current_name = 'ADM_Mewtwo'
        """)
        
        await conn.execute(stmt, {"dt": expire_date})
        print("✅ Executed update successfully.")

if __name__ == "__main__":
    asyncio.run(fix_mewtwo_naive())
