
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.players_registry_v2 import SentinelPlayerRegistry
from sqlalchemy.ext.asyncio import AsyncSession

async def check_duplicates():
    async with AsyncSession(engine) as session:
        print("--- Checking for ADM_Mewtwo Duplicates ---")
        q = select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.current_name == 'ADM_Mewtwo')
        res = await session.execute(q)
        players = res.scalars().all()
        
        for p in players:
            print(f"SteamID: {p.steam_id} | Name: {p.current_name} | Phone: {p.phone_number} | Tier: {p.plan_tier}")
        
        if len(players) > 1:
            print("⚠️ DUPLICATES DETECTED!")
        else:
            print("No duplicates found by current_name.")
            
        print("\n--- Fixing Premium via SteamID (76561198071690900) ---")
        # Ensure we update the correct SteamID
        target_steam = "76561198071690900"
        p_target = await session.get(SentinelPlayerRegistry, target_steam)
        if p_target:
            from datetime import datetime, timedelta
            p_target.plan_tier = 'premium'
            p_target.plan_expires_at = datetime.utcnow() + timedelta(days=30)
            session.add(p_target)
            await session.commit()
            print(f"✅ Fixed SteamID {target_steam} to Premium. Expires: {p_target.plan_expires_at}")
        else:
            print(f"❌ SteamID {target_steam} NOT FOUND!")

if __name__ == "__main__":
    asyncio.run(check_duplicates())
