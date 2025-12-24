from sqlmodel import select
from app.core.database import engine
from app.models.system_v2 import SentinelProcessedFile
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

async def check():
    async with AsyncSession(engine) as session:
        # Check last few admin files
        stmt = select(SentinelProcessedFile).where(SentinelProcessedFile.log_type == "Admin").order_by(SentinelProcessedFile.processed_at.desc()).limit(5)
        res = await session.execute(stmt)
        files = res.scalars().all()
        
        print(f"Checking processed Admin files:")
        for f in files:
            print(f"File: {f.filename}, Lines: {f.lines_processed}, Status: {f.status}")

if __name__ == "__main__":
    asyncio.run(check())
