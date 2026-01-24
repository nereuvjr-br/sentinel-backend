import asyncio
from sqlmodel import SQLModel
from app.core.database import engine
from app.models.access_request import SentinelAccessRequest

async def update_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(update_db())
