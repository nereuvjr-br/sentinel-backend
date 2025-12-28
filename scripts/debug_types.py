
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def check_types():
    async with AsyncSession(engine) as session:
        res = await session.execute(text("SELECT DISTINCT trade_type FROM sentinel_economy_trades"))
        print(f"TYPES: {[r[0] for r in res.fetchall()]}")

if __name__ == "__main__":
    asyncio.run(check_types())
