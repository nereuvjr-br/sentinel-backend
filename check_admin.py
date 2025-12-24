from sqlmodel import select, func
from app.core.database import engine
from app.models.admin_v2 import SentinelAdminCommand
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

async def check_admin():
    async with AsyncSession(engine) as session:
        stmt = select(func.count()).select_from(SentinelAdminCommand)
        res = await session.execute(stmt)
        print(f"ADMIN COMMANDS: {res.scalar()}")

if __name__ == "__main__":
    asyncio.run(check_admin())
