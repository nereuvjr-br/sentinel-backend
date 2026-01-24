
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.economy_v2 import SentinelUnparsedLog
from app.models.gameplay_v2 import SentinelRaidMinigame
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

async def check_missing():
    async with AsyncSession(engine) as session:
        print("--- Checking Latest 10 Unparsed Gameplay Logs ---")
        q = select(SentinelUnparsedLog).where(SentinelUnparsedLog.log_type == "Gameplay").order_by(desc(SentinelUnparsedLog.id)).limit(10)
        res = await session.execute(q)
        unparsed = res.scalars().all()
        for u in unparsed:
            print(f"UNPARSED [ID:{u.id}] Time:{u.created_at} | Err: {u.error_message} | Content: {u.raw_line[:150]}")
            
        print("\n--- Checking Latest 10 Raids ---")
        q2 = select(SentinelRaidMinigame).order_by(desc(SentinelRaidMinigame.timestamp)).limit(10)
        res2 = await session.execute(q2)
        raids = res2.scalars().all()
        for r in raids:
            print(f"RAID [ID:{r.id}] Time:{r.timestamp} | Atk: {r.attacker_name} | Success: {r.is_success} | Processed: {r.processed_at}")

if __name__ == "__main__":
    asyncio.run(check_missing())
