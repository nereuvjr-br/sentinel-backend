"""
Migração: Adicionar colunas de notificação (phone_number, whatsapp_group_id)
Data: 2026-01-17
"""

import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add parent dir to path to import app.core.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

async def migrate():
    # Ajusta a URL para o driver Async
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        print("🔧 Iniciando migração de notificações...")
        
        # 1. sentinel_players_registry -> phone_number
        check_player_col = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sentinel_players_registry' 
            AND column_name = 'phone_number'
        """)
        result = await conn.execute(check_player_col)
        if result.fetchone():
            print("✅ Coluna 'phone_number' já existe em 'sentinel_players_registry'.")
        else:
            print("➕ Adicionando coluna 'phone_number' em 'sentinel_players_registry'...")
            await conn.execute(text("ALTER TABLE sentinel_players_registry ADD COLUMN phone_number VARCHAR(50)"))
            print("✅ Adicionada!")

        # 2. sentinel_clans -> whatsapp_group_id
        check_clan_col = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sentinel_clans' 
            AND column_name = 'whatsapp_group_id'
        """)
        result = await conn.execute(check_clan_col)
        if result.fetchone():
            print("✅ Coluna 'whatsapp_group_id' já existe em 'sentinel_clans'.")
        else:
            print("➕ Adicionando coluna 'whatsapp_group_id' em 'sentinel_clans'...")
            await conn.execute(text("ALTER TABLE sentinel_clans ADD COLUMN whatsapp_group_id VARCHAR(255)"))
            print("✅ Adicionada!")
            
    await engine.dispose()
    print("✅ Migração de notificações concluída!")

if __name__ == "__main__":
    asyncio.run(migrate())
