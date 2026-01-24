
import asyncio
from sqlmodel import select, col
from app.core.database import engine
from app.models.economy_v2 import SentinelUnparsedLog
from app.models.gameplay_v2 import SentinelRaidMinigame
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, text

async def investigate_pombo():
    async with AsyncSession(engine) as session:
        print("--- Investigating 'pombo' Activity (Last 20 mins) ---")
        
        # 1. PARSED RAIDS
        print("\n[PARSED RAIDS]")
        q = select(SentinelRaidMinigame).where(col(SentinelRaidMinigame.attacker_name).contains("pombo")).order_by(desc(SentinelRaidMinigame.timestamp)).limit(20)
        res = await session.execute(q)
        raids = res.scalars().all()
        for r in raids:
            print(f"✅ ID:{r.id} | {r.timestamp} | Success:{r.is_success} | Target:{r.target_owner_name}")
            
        # 2. UNPARSED LOGS (Containing 'pombo')
        print("\n[UNPARSED LOGS with 'pombo']")
        # RAW SQL because 'contains' might not work well on all fields or mapped classes depending on setup, being safe.
        stmt = text("SELECT id, raw_line, error_message FROM sentinel_unparsed_logs WHERE raw_line LIKE '%pombo%' ORDER BY id DESC LIMIT 20")
        res_un = await session.execute(stmt)
        unparsed = res_un.fetchall()
        
        if not unparsed:
            print("No unparsed logs found containing 'pombo'.")
            
        for u in unparsed:
             print(f"⚠️ ID:{u.id} | Err:{u.error_message} | Line:{u.raw_line.strip()[:100]}...")

if __name__ == "__main__":
    asyncio.run(investigate_pombo())
