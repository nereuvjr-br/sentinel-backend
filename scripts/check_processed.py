import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def check():
    async with AsyncSession(engine) as s:
        r = await s.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='sentinel_processed_files' ORDER BY ordinal_position"))
        cols = [row[0] for row in r.fetchall()]
        print("Colunas em sentinel_processed_files:")
        for col in cols:
            print(f"  - {col}")
        
        # Ver dados
        r2 = await s.execute(text("SELECT * FROM sentinel_processed_files LIMIT 5"))
        rows = r2.fetchall()
        print(f"\nTotal de arquivos processados: {len(rows)}")
        for row in rows:
            print(f"  {row}")

asyncio.run(check())
