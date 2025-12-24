from app.core.database import engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

async def migrate():
    print("🔄 Migrando sentinel_processed_files...")
    async with AsyncSession(engine) as session:
        await session.execute(text("ALTER TABLE sentinel_processed_files ADD COLUMN IF NOT EXISTS processed_bytes BIGINT DEFAULT 0"))
        await session.execute(text("ALTER TABLE sentinel_processed_files ADD COLUMN IF NOT EXISTS last_modified TIMESTAMP DEFAULT NOW()"))
        await session.commit()
    print("✅ Migração Concluída.")

if __name__ == "__main__":
    asyncio.run(migrate())
