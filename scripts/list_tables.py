"""
Script para listar todas as tabelas do banco sentinel_dev
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def list_tables():
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    
    async with AsyncSession(engine) as session:
        result = await session.execute(text(query))
        tables = result.fetchall()
        
        print(f"\n📊 Total de tabelas no banco sentinel_dev: {len(tables)}\n")
        print("=" * 60)
        
        for idx, (table_name,) in enumerate(tables, 1):
            print(f"{idx:2d}. {table_name}")
        
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(list_tables())
