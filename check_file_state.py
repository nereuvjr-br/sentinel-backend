
import asyncio
from sqlmodel import select, col
from app.core.database import engine
from app.models.system_v2 import SentinelProcessedFile
from sqlalchemy.ext.asyncio import AsyncSession

async def check_recent_processed():
    print(f"Checking recently processed files...")
    
    async with AsyncSession(engine) as session:
        stmt = select(SentinelProcessedFile).order_by(col(SentinelProcessedFile.last_modified).desc()).limit(10)
        result = await session.execute(stmt)
        files = result.scalars().all()
        
        if files:
            print(f"✅ Found {len(files)} recent records:")
            for pf in files:
                print(f" - {pf.filename} | Bytes: {pf.processed_bytes} | Modified: {pf.last_modified}")
        else:
            print("❌ No processed files found.")

if __name__ == "__main__":
    asyncio.run(check_recent_processed())
