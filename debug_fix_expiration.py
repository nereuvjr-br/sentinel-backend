
import asyncio
from datetime import datetime, timedelta
from sqlmodel import select
from app.core.database import engine
from app.models.players_registry_v2 import SentinelPlayerRegistry
from sqlalchemy.ext.asyncio import AsyncSession

async def check():
    async with AsyncSession(engine) as session:
        print("--- Checking Player 'ADM_Sabugador' Details ---")
        q = select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.current_name == 'ADM_Sabugador')
        res = await session.execute(q)
        p = res.scalars().first()
        
        if p:
            print(f'Name: {p.current_name}')
            print(f'Tier: {p.plan_tier}')
            print(f'Expires At: {p.plan_expires_at}')
            
            if p.plan_tier == 'premium' and not p.plan_expires_at:
                print("\n⚠️ Problem detected: Premium tier but NO expiration date! Setting to 30 days from now...")
                p.plan_expires_at = datetime.utcnow() + timedelta(days=30)
                session.add(p)
                await session.commit()
                print("✅ Fixed: Expiration date set.")
            elif p.plan_expires_at and p.plan_expires_at < datetime.utcnow():
                 print("\n⚠️ Problem detected: Plan Expired!")
                 # Optional: panic fix extend?
                 # p.plan_expires_at = datetime.utcnow() + timedelta(days=30)
                 # session.add(p)
                 # await session.commit()

        else:
            print("Player not found")

if __name__ == "__main__":
    asyncio.run(check())
