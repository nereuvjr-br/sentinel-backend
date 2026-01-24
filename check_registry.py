
import asyncio
from sqlmodel import select, func
from app.core.database import engine
from app.models.clan_v2 import SentinelClan
from app.models.players_registry_v2 import SentinelPlayerRegistry
from sqlalchemy.ext.asyncio import AsyncSession

async def check_registry_counts():
    print(f"Checking Registry Data (SCUM.db sourced)...")
    
    async with AsyncSession(engine) as session:
        # Check Clans
        clans_count = (await session.execute(select(func.count(SentinelClan.id)))).scalar_one()
        print(f"✅ Total Clans in DB: {clans_count}")
        
        if clans_count > 0:
            clans = (await session.execute(select(SentinelClan.name).limit(5))).scalars().all()
            print(f"   Sample Clans: {clans}")

        # Check Players
        players_count = (await session.execute(select(func.count(SentinelPlayerRegistry.steam_id)))).scalar_one()
        print(f"✅ Total Players in Registry: {players_count}")
        
        if players_count > 0:
            players = (await session.execute(select(SentinelPlayerRegistry.current_name).limit(5))).scalars().all()
            print(f"   Sample Players: {players}")

if __name__ == "__main__":
    asyncio.run(check_registry_counts())
