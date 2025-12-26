import asyncio
import logging
from sqlmodel import select, col
# Silence SQL Logs
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from app.core.database import engine
from app.models.system_v2 import SentinelProcessedFile
from sqlalchemy.ext.asyncio import AsyncSession

async def main():
    async with AsyncSession(engine) as session:
        print("--- Checking Processed Files Timestamps ---")
        try:
            stmt = select(SentinelProcessedFile).order_by(col(SentinelProcessedFile.last_modified).desc()).limit(5)
            result = await session.execute(stmt)
            files = result.scalars().all()
            
            for f in files:
                print(f"File: {f.filename} | Modified: {f.last_modified} | Lines: {f.lines_processed} | Status: {f.status}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
