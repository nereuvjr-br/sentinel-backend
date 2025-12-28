
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def check_unparsed():
    async with AsyncSession(engine) as session:
        print("=== ÚLTIMOS ERROS (UNPARSED) ===")
        res = await session.execute(text("SELECT filename, raw_line, error_message FROM sentinel_unparsed_logs ORDER BY id DESC LIMIT 10"))
        rows = res.fetchall()
        for r in rows:
            print(f"\nExample File: {r.filename}")
            print(f"Error: {r.error_message}")
            print(f"Line Start: {r.raw_line[:100]}...")

if __name__ == "__main__":
    asyncio.run(check_unparsed())
