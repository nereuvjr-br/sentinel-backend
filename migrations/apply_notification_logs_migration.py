"""
Script para aplicar a migração da tabela sentinel_notification_logs
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def apply_migration():
    migration_commands = [
        """
        CREATE TABLE IF NOT EXISTS sentinel_notification_logs (
            id SERIAL PRIMARY KEY,
            sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            notification_type VARCHAR(50) NOT NULL,
            recipient_phone VARCHAR(20) NOT NULL,
            recipient_type VARCHAR(20) NOT NULL,
            recipient_steam_id VARCHAR(50),
            recipient_name VARCHAR(255),
            message_content TEXT NOT NULL,
            event_context JSONB,
            status VARCHAR(20) NOT NULL,
            error_message TEXT,
            api_response_code INTEGER,
            api_response_body TEXT,
            evolution_instance VARCHAR(100),
            retry_count INTEGER DEFAULT 0
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_notif_sent_at ON sentinel_notification_logs(sent_at)",
        "CREATE INDEX IF NOT EXISTS idx_notif_type ON sentinel_notification_logs(notification_type)",
        "CREATE INDEX IF NOT EXISTS idx_notif_recipient_phone ON sentinel_notification_logs(recipient_phone)",
        "CREATE INDEX IF NOT EXISTS idx_notif_recipient_steam_id ON sentinel_notification_logs(recipient_steam_id)",
        "CREATE INDEX IF NOT EXISTS idx_notif_status ON sentinel_notification_logs(status)"
    ]
    
    async with AsyncSession(engine) as session:
        try:
            for cmd in migration_commands:
                await session.execute(text(cmd))
            await session.commit()
            print("✅ Migração aplicada com sucesso: sentinel_notification_logs criada!")
        except Exception as e:
            print(f"❌ Erro ao aplicar migração: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(apply_migration())
