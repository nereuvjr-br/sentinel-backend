from sqlmodel import delete
from app.core.database import engine
from app.models.system_v2 import SentinelProcessedFile
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

async def reset():
    async with AsyncSession(engine) as session:
        stmt = delete(SentinelProcessedFile).where(SentinelProcessedFile.log_type == "Admin")
        await session.execute(stmt)
        await session.commit()
        print("Resetado admin_20251223060055.log")

if __name__ == "__main__":
    asyncio.run(reset())
