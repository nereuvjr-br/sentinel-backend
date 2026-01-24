
import asyncio
from sqlmodel import select, col
from app.core.database import engine
from app.models.economy_v2 import SentinelUnparsedLog
from app.models.gameplay_v2 import SentinelRaidMinigame
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, text

async def investigate_locks():
    async with AsyncSession(engine) as session:
        print("--- Investigating 'Basic' Locks & Recent Raids ---")
        
        # 1. PARSED RAIDS (Last 20)
        print("\n[PARSED RAIDS - CHECK LOCK TYPE]")
        q = select(SentinelRaidMinigame).order_by(desc(SentinelRaidMinigame.timestamp)).limit(20)
        res = await session.execute(q)
        raids = res.scalars().all()
        for r in raids:
            print(f"I:{r.id} | {r.timestamp.strftime('%H:%M:%S')} | Atk: {r.attacker_name:<15} | Lock: {r.lock_type:<10} | Succ: {r.is_success}")
            
        # 2. UNPARSED LOGS (Containing 'Basic' or 'Lock')
        print("\n[UNPARSED LOGS search 'Basic']")
        stmt = text("SELECT id, raw_line, error_message FROM sentinel_unparsed_logs WHERE raw_line LIKE '%Basic%' ORDER BY id DESC LIMIT 20")
        res_un = await session.execute(stmt)
        unparsed = res_un.fetchall()
        
        if not unparsed:
            print("No unparsed logs found containing 'Basic'.")
            
        for u in unparsed:
             print(f"⚠️ ID:{u.id} | Err:{u.error_message} | Line:{u.raw_line.strip()[:100]}...")

if __name__ == "__main__":
    asyncio.run(investigate_locks())
