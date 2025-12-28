
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def fix_processed_files_table():
    async with AsyncSession(engine) as session:
        print("🔧 Adicionando coluna log_type em sentinel_processed_files...")
        try:
            # Tentar adicionar a coluna
            await session.execute(text("ALTER TABLE sentinel_processed_files ADD COLUMN IF NOT EXISTS log_type VARCHAR(50)"))
            await session.commit()
            print("✅ Coluna adicionada (ou já existia) com sucesso.")
        except Exception as e:
            print(f"❌ Erro ao alterar tabela: {e}")

if __name__ == "__main__":
    asyncio.run(fix_processed_files_table())
