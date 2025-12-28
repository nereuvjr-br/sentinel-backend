"""
Script para corrigir a tabela sentinel_processed_files
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def fix_processed_files_table():
    print("🔧 Corrigindo tabela sentinel_processed_files...\n")
    
    async with AsyncSession(engine) as session:
        try:
            # 1. Drop tabela antiga
            print("1. Removendo tabela antiga...")
            await session.execute(text("DROP TABLE IF EXISTS sentinel_processed_files CASCADE"))
            await session.commit()
            print("   ✅ Tabela antiga removida\n")
            
            # 2. Criar nova tabela com schema correto
            print("2. Criando nova tabela com schema correto...")
            await session.execute(text("""
                CREATE TABLE sentinel_processed_files (
                    filename VARCHAR(255) PRIMARY KEY,
                    last_offset BIGINT DEFAULT 0,
                    last_size BIGINT DEFAULT 0,
                    last_processed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            await session.commit()
            print("   ✅ Nova tabela criada\n")
            
            # 3. Criar índice
            print("3. Criando índice...")
            await session.execute(text("""
                CREATE INDEX idx_processed_files_last_processed 
                ON sentinel_processed_files(last_processed)
            """))
            await session.commit()
            print("   ✅ Índice criado\n")
            
            # 4. Verificar
            print("4. Verificando estrutura...")
            result = await session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name='sentinel_processed_files' 
                ORDER BY ordinal_position
            """))
            cols = result.fetchall()
            
            print("   Colunas:")
            for col in cols:
                print(f"     - {col[0]:20} ({col[1]})")
            
            print("\n✅ Tabela sentinel_processed_files corrigida com sucesso!")
            print("\n💡 Próximo passo: Reinicie o daemon para processar novamente")
            
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(fix_processed_files_table())
