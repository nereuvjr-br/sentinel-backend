import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def check_errors():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT raw_line, error_message, timestamp 
            FROM sentinel_unparsed_logs 
            WHERE log_type = 'SYSTEM_ERROR' 
            ORDER BY timestamp DESC 
            LIMIT 3
        """))
        
        rows = result.fetchall()
        
        if rows:
            print("\n🔴 ERROS DO SISTEMA:\n")
            for i, row in enumerate(rows, 1):
                print(f"--- Erro #{i} ({row[2]}) ---")
                print(f"Mensagem: {row[1]}")
                print(f"Traceback (primeiras 500 chars):\n{row[0][:500]}\n")
        else:
            print("✅ Nenhum erro do sistema encontrado!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_errors())
