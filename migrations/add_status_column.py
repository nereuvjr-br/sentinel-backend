"""
Migração: Adicionar coluna 'status' à tabela sentinel_processed_files
Data: 2025-12-26
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def migrate():
    # Ajusta a URL para o driver Async
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        print("🔧 Verificando se a coluna 'status' existe...")
        
        # Verificar se a coluna já existe
        check_column = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sentinel_processed_files' 
            AND column_name = 'status'
        """)
        
        result = await conn.execute(check_column)
        exists = result.fetchone()
        
        if exists:
            print("✅ Coluna 'status' já existe!")
        else:
            print("➕ Adicionando coluna 'status'...")
            
            # Adicionar a coluna
            add_column = text("""
                ALTER TABLE sentinel_processed_files 
                ADD COLUMN status VARCHAR DEFAULT 'Completed'
            """)
            
            await conn.execute(add_column)
            print("✅ Coluna 'status' adicionada com sucesso!")
    
    await engine.dispose()
    print("✅ Migração concluída!")

if __name__ == "__main__":
    asyncio.run(migrate())
