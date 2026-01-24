
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.players_registry_v2 import SentinelPlayerRegistry
from sqlalchemy.ext.asyncio import AsyncSession

async def check():
    async with AsyncSession(engine) as session:
        print("--- Checking Player 'ADM_Sabugador' ---")
        # Check by Name
        q = select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.current_name == 'ADM_Sabugador')
        res = await session.execute(q)
        p = res.scalars().first()
        if p:
            print(f'Found by Name: ID={p.steam_id}, Name={p.current_name}, Phone={p.phone_number}, Tier={getattr(p, "plan_tier", "N/A")}')
        else:
            print("Not found by name 'ADM_Sabugador'")
        
        print("\n--- Checking Phone '5511998289270' ---")
        # Check by Phone
        q2 = select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.phone_number == '5511998289270')
        res2 = await session.execute(q2)
        p2 = res2.scalars().first()
        if p2:
            print(f'Found by Phone: ID={p2.steam_id}, Name={p2.current_name}, Phone={p2.phone_number}, Tier={getattr(p2, "plan_tier", "N/A")}')
        else:
             print("Not found by phone '5511998289270'")
        
        # Also check update capability
        if p:
            print("\n--- Updating to PREMIUM ---")
            p.plan_tier = 'premium'
            session.add(p)
            await session.commit()
            print("Updated successfully.")

if __name__ == "__main__":
    asyncio.run(check())
