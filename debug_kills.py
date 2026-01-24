
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.kill_v2 import SentinelKill
from app.models.system_v2 import SentinelProcessedFile
from app.models.economy_v2 import SentinelUnparsedLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

async def check_kills_health():
    async with AsyncSession(engine) as session:
        print("--- KILL FEED HEALTH CHECK ---")
        
        # 1. Latest 5 Kills
        print("\n[LATEST 5 KILLS]")
        kills = (await session.execute(select(SentinelKill).order_by(desc(SentinelKill.timestamp)).limit(5))).scalars().all()
        for k in kills:
            print(f"💀 Time: {k.timestamp} | Killer: {k.killer_name} -> Victim: {k.victim_name} | Weapon: {k.weapon}")
            
        # 2. Processed File State
        print("\n[PROCESSED FILES STATE]")
        files = (await session.execute(select(SentinelProcessedFile).where(SentinelProcessedFile.filename.contains("kill")))).scalars().all()
        for f in files:
            print(f"📂 File: {f.filename}")
            print(f"   Processed Checkpoint: {f.processed_bytes} bytes")
            print(f"   Lines Processed: {f.lines_processed}")
            print(f"   Last Modified: {f.last_modified}")

        # 3. Recent Errors
        print("\n[RECENT KILL PARSER ERRORS]")
        q = select(SentinelUnparsedLog).where(SentinelUnparsedLog.filename.contains("kill")).order_by(desc(SentinelUnparsedLog.id)).limit(5)
        logs = (await session.execute(q)).scalars().all()
        for l in logs:
            print(f"⚠️ ID:{l.id} | Err: {l.error_message} | Line: {l.raw_line[:50]}...")

if __name__ == "__main__":
    asyncio.run(check_kills_health())
