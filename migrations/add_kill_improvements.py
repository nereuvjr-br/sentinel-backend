"""
Script para adicionar melhorias à tabela de kills
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def add_kill_improvements():
    alterations = [
        # Weapon Details
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS weapon_class VARCHAR(255)",
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS damage_type VARCHAR(50)",
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS weapon_category VARCHAR(50)",
        
        # NPC Detection
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS killer_is_npc BOOLEAN DEFAULT FALSE",
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS killer_npc_type VARCHAR(50)",
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS victim_is_npc BOOLEAN DEFAULT FALSE",
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS victim_npc_type VARCHAR(50)",
        
        # Advanced Features
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS is_revenge_kill BOOLEAN DEFAULT FALSE",
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS revenge_for_kill_id INTEGER",
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS kill_streak_id INTEGER",
        
        # Hotspots (Grid-based)
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS grid_x INTEGER",
        "ALTER TABLE sentinel_kills ADD COLUMN IF NOT EXISTS grid_y INTEGER",
    ]
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_kills_weapon_class ON sentinel_kills(weapon_class)",
        "CREATE INDEX IF NOT EXISTS idx_kills_weapon_category ON sentinel_kills(weapon_category)",
        "CREATE INDEX IF NOT EXISTS idx_kills_damage_type ON sentinel_kills(damage_type)",
        "CREATE INDEX IF NOT EXISTS idx_kills_killer_npc ON sentinel_kills(killer_is_npc)",
        "CREATE INDEX IF NOT EXISTS idx_kills_victim_npc ON sentinel_kills(victim_is_npc)",
        "CREATE INDEX IF NOT EXISTS idx_kills_grid ON sentinel_kills(grid_x, grid_y)",
        "CREATE INDEX IF NOT EXISTS idx_kills_revenge ON sentinel_kills(is_revenge_kill) WHERE is_revenge_kill = TRUE",
    ]
    
    async with AsyncSession(engine) as session:
        print("🚀 Adicionando melhorias à tabela sentinel_kills...\n")
        
        # Adicionar colunas
        print("📝 Adicionando novas colunas...")
        for idx, sql in enumerate(alterations, 1):
            try:
                await session.execute(text(sql))
                await session.commit()
                print(f"  ✅ [{idx}/{len(alterations)}] Coluna adicionada")
            except Exception as e:
                await session.rollback()
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    print(f"  ℹ️  [{idx}/{len(alterations)}] Coluna já existe")
                else:
                    print(f"  ⚠️  [{idx}/{len(alterations)}] Erro: {str(e)[:60]}")
        
        # Criar índices
        print("\n🔧 Criando índices...")
        success = 0
        for idx, sql in enumerate(indexes, 1):
            try:
                await session.execute(text(sql))
                await session.commit()
                success += 1
                print(f"  ✅ [{idx}/{len(indexes)}] Índice criado")
            except Exception as e:
                await session.rollback()
                if "already exists" in str(e):
                    print(f"  ℹ️  [{idx}/{len(indexes)}] Índice já existe")
                else:
                    print(f"  ⚠️  [{idx}/{len(indexes)}] Erro: {str(e)[:60]}")
        
        print(f"\n✅ Melhorias aplicadas! {success} índices criados.")
        print("\n📊 Novas funcionalidades:")
        print("  - Separação de weapon class e damage type")
        print("  - Categorização de armas")
        print("  - Detecção automática de NPCs")
        print("  - Suporte para revenge kills")
        print("  - Suporte para kill streaks")
        print("  - Grid para hotspots de PvP")

if __name__ == "__main__":
    asyncio.run(add_kill_improvements())
