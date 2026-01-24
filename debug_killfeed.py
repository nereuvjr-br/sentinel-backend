
import asyncio
from sqlmodel import select
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.models.kill_v2 import SentinelKill
from app.models.system_v2 import SentinelProcessedFile
from app.models.economy_v2 import SentinelUnparsedLog
from datetime import datetime

async def debug_killfeed():
    async with AsyncSession(engine) as session:
        print(f"Time Now: {datetime.utcnow()}")
        
        print("\n--- LATEST PROCESSED KILL FILES ---")
        stmt = select(SentinelProcessedFile).where(SentinelProcessedFile.log_type == 'Kill').order_by(desc(SentinelProcessedFile.last_modified)).limit(3)
        files = (await session.execute(stmt)).scalars().all()
        for f in files:
            print(f"File: {f.filename} | Mod: {f.last_modified} | Events: {f.lines_processed} | Bytes: {f.processed_bytes}")

        print("\n--- LATEST KILLS IN DB ---")
        stmt = select(SentinelKill).order_by(desc(SentinelKill.timestamp)).limit(5)
        kills = (await session.execute(stmt)).scalars().all()
        for k in kills:
            print(f"Kill: {k.timestamp} | {k.killer_name} -> {k.victim_name} | Weapon: {k.weapon}")

        print("\n--- RECENT ERRORS ---")
        stmt = select(SentinelUnparsedLog).where(SentinelUnparsedLog.log_type == "SYSTEM_ERROR").order_by(desc(SentinelUnparsedLog.id)).limit(3)
        errors = (await session.execute(stmt)).scalars().all()
        for e in errors:
            print(f"[{e.timestamp}] {e.error_message}")

if __name__ == "__main__":
    asyncio.run(debug_killfeed())
