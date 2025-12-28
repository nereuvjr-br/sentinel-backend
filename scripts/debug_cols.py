
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def check_cols():
    async with AsyncSession(engine) as session:
        try:
            # Tentar pegar 1 registro para ver keys
            res = await session.execute(text("SELECT * FROM sentinel_economy_trades LIMIT 1"))
            print(f"COLUNAS: {res.keys()}")
        except Exception as e:
            print(f"Erro: {e}")
            # Tentar describe
            try:
                res = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'sentinel_economy_trades'"))
                print("Columns from schema:", [r[0] for r in res.fetchall()])
            except:
                pass

if __name__ == "__main__":
    asyncio.run(check_cols())
