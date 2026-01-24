
import asyncio
from datetime import datetime, timedelta
from app.core.database import engine
from sqlalchemy import text

async def fix_mewtwo_final():
    async with engine.begin() as conn:
        print("--- Updating ADM_Mewtwo by SteamID (Final) ---")
        
        # Use naive UTC time + 30 days
        expire_date = datetime.utcnow() + timedelta(days=30)
        target_steam = "76561198071690900"
        
        stmt = text("""
            UPDATE sentinel_players_registry 
            SET plan_tier = 'premium', plan_expires_at = :dt 
            WHERE steam_id = :sid
        """)
        
        await conn.execute(stmt, {"dt": expire_date, "sid": target_steam})
        print(f"✅ Executed update successfully for {target_steam}.")

if __name__ == "__main__":
    asyncio.run(fix_mewtwo_final())
