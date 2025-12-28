"""
Script para criar tabela de ações econômicas de admin
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def create_table():
    sql = """
    CREATE TABLE IF NOT EXISTS sentinel_admin_economy_actions (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP NOT NULL,
        
        -- Admin Info
        admin_steam_id VARCHAR(255) NOT NULL,
        admin_name VARCHAR(255) NOT NULL,
        admin_game_id VARCHAR(50),
        
        -- Action Details
        action_type VARCHAR(50) NOT NULL,
        raw_command TEXT NOT NULL,
        
        -- Economic Impact
        item_class VARCHAR(255),
        item_quantity INTEGER,
        stack_count INTEGER,
        economic_value DOUBLE PRECISION,
        
        -- Target
        target_steam_id VARCHAR(255),
        target_name VARCHAR(255),
        
        -- Location
        location JSONB,
        
        -- Impact Classification
        impact_level VARCHAR(20),
        is_cash_spawn BOOLEAN DEFAULT FALSE,
        is_weapon_spawn BOOLEAN DEFAULT FALSE,
        
        -- Metadata
        is_automated BOOLEAN DEFAULT FALSE,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_admin_eco_timestamp ON sentinel_admin_economy_actions(timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_admin_eco_admin ON sentinel_admin_economy_actions(admin_steam_id)",
        "CREATE INDEX IF NOT EXISTS idx_admin_eco_action ON sentinel_admin_economy_actions(action_type)",
        "CREATE INDEX IF NOT EXISTS idx_admin_eco_impact ON sentinel_admin_economy_actions(impact_level)",
        "CREATE INDEX IF NOT EXISTS idx_admin_eco_cash ON sentinel_admin_economy_actions(is_cash_spawn) WHERE is_cash_spawn = TRUE",
        "CREATE INDEX IF NOT EXISTS idx_admin_eco_item ON sentinel_admin_economy_actions(item_class)",
    ]
    
    async with AsyncSession(engine) as session:
        print("🚀 Criando tabela sentinel_admin_economy_actions...\n")
        
        try:
            # Criar tabela
            await session.execute(text(sql))
            await session.commit()
            print("  ✅ Tabela criada com sucesso!")
            
            # Criar índices
            print("\n🔧 Criando índices...")
            for idx, index_sql in enumerate(indexes, 1):
                try:
                    await session.execute(text(index_sql))
                    await session.commit()
                    print(f"  ✅ [{idx}/{len(indexes)}] Índice criado")
                except Exception as e:
                    await session.rollback()
                    if "already exists" in str(e):
                        print(f"  ℹ️  [{idx}/{len(indexes)}] Índice já existe")
                    else:
                        print(f"  ⚠️  [{idx}/{len(indexes)}] Erro: {str(e)[:60]}")
            
            print("\n✅ Implementação concluída!")
            print("\n📊 Nova tabela:")
            print("  - sentinel_admin_economy_actions")
            print("\n🎯 Funcionalidades:")
            print("  - Rastreamento de spawns de dinheiro")
            print("  - Auditoria de spawns de armas")
            print("  - Classificação de impacto econômico")
            print("  - Detecção de abuso de admin")
            
        except Exception as e:
            await session.rollback()
            if "already exists" in str(e):
                print("  ℹ️  Tabela já existe")
            else:
                print(f"  ❌ Erro: {e}")
                raise

if __name__ == "__main__":
    asyncio.run(create_table())
