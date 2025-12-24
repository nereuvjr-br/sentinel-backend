
import asyncio
import sys
sys.path.insert(0, '/home/nereu-jr/Área de trabalho/scum/SCUMSentinel/backend')
from app.core.database import engine
from sqlalchemy import text

async def check_trades():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT count(*) FROM sentinel_economy_trades"))
        count = result.scalar()
        print(f"Total Trades: {count}")
        
        result = await conn.execute(text("SELECT timestamp FROM sentinel_economy_trades ORDER BY timestamp ASC LIMIT 1"))
        first = result.scalar()
        print(f"Oldest Trade: {first}")

if __name__ == "__main__":
    asyncio.run(check_trades())
