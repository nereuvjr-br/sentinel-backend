"""
Script para aplicar a migração da tabela sentinel_vehicles
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def apply_migration():
    migration_commands = [
        """
        CREATE TABLE IF NOT EXISTS sentinel_vehicles (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            vehicle_id VARCHAR(255) NOT NULL,
            vehicle_class VARCHAR(255) NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            owner_id VARCHAR(255),
            owner_name VARCHAR(255),
            location JSONB,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_vehicles_timestamp ON sentinel_vehicles(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_vehicles_vehicle_id ON sentinel_vehicles(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_vehicles_vehicle_class ON sentinel_vehicles(vehicle_class)",
        "CREATE INDEX IF NOT EXISTS idx_vehicles_owner_id ON sentinel_vehicles(owner_id)",
        "CREATE INDEX IF NOT EXISTS idx_vehicles_event_type ON sentinel_vehicles(event_type)"
    ]
    
    async with AsyncSession(engine) as session:
        try:
            for cmd in migration_commands:
                await session.execute(text(cmd))
            await session.commit()
            print("✅ Migração aplicada com sucesso: sentinel_vehicles criada!")
        except Exception as e:
            print(f"❌ Erro ao aplicar migração: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(apply_migration())
