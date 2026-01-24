
import asyncio
from datetime import datetime, timedelta
from sqlmodel import select
from app.core.database import engine
from app.models.players_registry_v2 import SentinelPlayerRegistry
from sqlalchemy.ext.asyncio import AsyncSession

async def fix_mewtwo():
    async with AsyncSession(engine) as session:
        print("--- Updating ADM_Mewtwo to Premium + 30 Days ---")
        q = select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.current_name == 'ADM_Mewtwo')
        res = await session.execute(q)
        p = res.scalars().first()
        
        if p:
            print(f"Current Status: {p.plan_tier}")
            p.plan_tier = 'premium'
            # Set 30 days from now
            p.plan_expires_at = datetime.utcnow() + timedelta(days=30)
            session.add(p)
            await session.commit()
            print(f"✅ Updated ADM_Mewtwo to Premium. Expires at: {p.plan_expires_at}")
        else:
            print("ADM_Mewtwo not found.")

if __name__ == "__main__":
    asyncio.run(fix_mewtwo())
