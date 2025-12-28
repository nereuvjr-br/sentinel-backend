"""
Script para criar tabelas de registro de jogadores
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def create_tables():
    tables_sql = [
        # 1. Players Registry
        """
        CREATE TABLE IF NOT EXISTS sentinel_players_registry (
            steam_id VARCHAR(255) PRIMARY KEY,
            
            -- Nome Atual
            current_name VARCHAR(255) NOT NULL,
            previous_names TEXT[],
            
            -- Squad/Clã
            squad_name VARCHAR(255),
            squad_tag VARCHAR(50),
            squad_joined_at TIMESTAMP,
            
            -- Estatísticas
            first_seen TIMESTAMP NOT NULL,
            last_seen TIMESTAMP NOT NULL,
            total_logins INTEGER DEFAULT 0,
            total_playtime_hours DOUBLE PRECISION DEFAULT 0,
            
            -- Flags
            is_active BOOLEAN DEFAULT TRUE,
            is_banned BOOLEAN DEFAULT FALSE,
            is_admin BOOLEAN DEFAULT FALSE,
            
            -- Metadados
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # 2. Name Changes
        """
        CREATE TABLE IF NOT EXISTS sentinel_name_changes (
            id SERIAL PRIMARY KEY,
            steam_id VARCHAR(255) NOT NULL,
            old_name VARCHAR(255),
            new_name VARCHAR(255) NOT NULL,
            changed_at TIMESTAMP NOT NULL,
            detected_in VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (steam_id) REFERENCES sentinel_players_registry(steam_id)
        )
        """
    ]
    
    indexes = [
        # Players Registry
        "CREATE INDEX IF NOT EXISTS idx_players_current_name ON sentinel_players_registry(current_name)",
        "CREATE INDEX IF NOT EXISTS idx_players_squad ON sentinel_players_registry(squad_name)",
        "CREATE INDEX IF NOT EXISTS idx_players_squad_tag ON sentinel_players_registry(squad_tag)",
        "CREATE INDEX IF NOT EXISTS idx_players_last_seen ON sentinel_players_registry(last_seen DESC)",
        "CREATE INDEX IF NOT EXISTS idx_players_first_seen ON sentinel_players_registry(first_seen)",
        "CREATE INDEX IF NOT EXISTS idx_players_active ON sentinel_players_registry(is_active)",
        
        # Name Changes
        "CREATE INDEX IF NOT EXISTS idx_name_changes_steam_id ON sentinel_name_changes(steam_id)",
        "CREATE INDEX IF NOT EXISTS idx_name_changes_date ON sentinel_name_changes(changed_at DESC)",
    ]
    
    table_names = [
        "sentinel_players_registry",
        "sentinel_name_changes"
    ]
    
    async with AsyncSession(engine) as session:
        print("🚀 Criando tabelas de registro de jogadores...\n")
        
        # Criar tabelas
        for idx, (sql, name) in enumerate(zip(tables_sql, table_names), 1):
            try:
                await session.execute(text(sql))
                await session.commit()
                print(f"  ✅ [{idx}/2] {name}")
            except Exception as e:
                await session.rollback()
                if "already exists" in str(e):
                    print(f"  ℹ️  [{idx}/2] {name} (já existe)")
                else:
                    print(f"  ❌ [{idx}/2] {name} - Erro: {str(e)[:80]}")
        
        # Criar índices
        print("\n🔧 Criando índices...")
        success = 0
        for idx, index_sql in enumerate(indexes, 1):
            try:
                await session.execute(text(index_sql))
                await session.commit()
                success += 1
                print(f"  ✅ [{idx}/{len(indexes)}] Índice criado")
            except Exception as e:
                await session.rollback()
                if "already exists" in str(e):
                    print(f"  ℹ️  [{idx}/{len(indexes)}] Índice já existe")
                else:
                    print(f"  ⚠️  [{idx}/{len(indexes)}] Erro: {str(e)[:60]}")
        
        print(f"\n✅ Implementação concluída! {success} índices criados.")
        print("\n📊 Novas tabelas:")
        print("  - sentinel_players_registry")
        print("  - sentinel_name_changes")
        print("\n🎯 Funcionalidades:")
        print("  - Rastreamento de histórico de nomes")
        print("  - Associação de squads/clãs")
        print("  - Detecção automática de mudanças de nome")
        print("  - Estatísticas de jogadores")

if __name__ == "__main__":
    asyncio.run(create_tables())
