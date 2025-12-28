"""
Migração: Adicionar colunas faltantes à tabela sentinel_processed_files
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
        print("🔧 Verificando colunas faltantes...")
        
        # Lista de colunas para verificar/adicionar
        columns_to_add = [
            ("last_modified", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("processed_bytes", "BIGINT DEFAULT 0"),
            ("lines_processed", "INTEGER DEFAULT 0"),
        ]
        
        for column_name, column_def in columns_to_add:
            # Verificar se a coluna já existe
            check_column = text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'sentinel_processed_files' 
                AND column_name = '{column_name}'
            """)
            
            result = await conn.execute(check_column)
            exists = result.fetchone()
            
            if exists:
                print(f"✅ Coluna '{column_name}' já existe!")
            else:
                print(f"➕ Adicionando coluna '{column_name}'...")
                
                # Adicionar a coluna
                add_column = text(f"""
                    ALTER TABLE sentinel_processed_files 
                    ADD COLUMN {column_name} {column_def}
                """)
                
                await conn.execute(add_column)
                print(f"✅ Coluna '{column_name}' adicionada com sucesso!")
    
    await engine.dispose()
    print("✅ Migração concluída!")

if __name__ == "__main__":
    asyncio.run(migrate())
