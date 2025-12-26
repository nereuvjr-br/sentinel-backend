from sqlmodel import delete
from app.core.database import engine
from app.models.system_v2 import SentinelProcessedFile
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

async def reset():
    print("🔄 Resetando estado dos arquivos de Gameplay...")
    async with AsyncSession(engine) as session:
        stmt = delete(SentinelProcessedFile).where(SentinelProcessedFile.log_type == "Gameplay")
        await session.execute(stmt)
        await session.commit()
    print("✅ Reset Concluído. O Daemon irá reprocessar Gameplay e capturar Explosivos/Bunkers.")

if __name__ == "__main__":
    asyncio.run(reset())
