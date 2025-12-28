"""
Script para criar views de análise de killfeeds
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def create_kill_views():
    views = [
        # 1. Player Kill Stats
        """
        CREATE OR REPLACE VIEW sentinel_player_kill_stats AS
        SELECT 
            killer_id,
            killer_name,
            
            -- Basic Stats
            COUNT(*) as total_kills,
            COUNT(*) FILTER (WHERE victim_is_npc = FALSE) as player_kills,
            COUNT(*) FILTER (WHERE victim_is_npc = TRUE) as npc_kills,
            
            -- Weapon Stats
            COUNT(DISTINCT weapon_category) as weapon_categories_used,
            MODE() WITHIN GROUP (ORDER BY weapon_category) as favorite_weapon_category,
            MODE() WITHIN GROUP (ORDER BY weapon_class) as favorite_weapon,
            
            -- Distance Stats
            AVG(distance) as avg_kill_distance,
            MAX(distance) as longest_kill,
            MIN(distance) FILTER (WHERE distance > 0) as shortest_kill,
            
            -- Time Stats
            COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 0 AND 6) as night_kills,
            COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 6 AND 18) as day_kills,
            COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 18 AND 24) as evening_kills,
            
            -- Anti-Cheat
            AVG(violation_score) as avg_violation_score,
            MAX(violation_score) as max_violation_score,
            
            -- Activity
            MIN(timestamp) as first_kill,
            MAX(timestamp) as last_kill,
            MAX(timestamp) - MIN(timestamp) as active_period
            
        FROM sentinel_kills
        WHERE killer_id IS NOT NULL
          AND killer_is_npc = FALSE
        GROUP BY killer_id, killer_name
        """,
        
        # 2. Weapon Meta Analysis
        """
        CREATE OR REPLACE VIEW sentinel_weapon_meta AS
        SELECT 
            weapon_category,
            weapon_class,
            damage_type,
            
            -- Kill Stats
            COUNT(*) as total_kills,
            COUNT(DISTINCT killer_id) as unique_users,
            
            -- Distance Stats
            AVG(distance) as avg_kill_distance,
            MAX(distance) as max_kill_distance,
            
            -- PvP vs PvE
            COUNT(*) FILTER (WHERE victim_is_npc = FALSE) as pvp_kills,
            COUNT(*) FILTER (WHERE victim_is_npc = TRUE) as pve_kills,
            
            -- Recent Activity (7 days)
            COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '7 days') as kills_last_7d,
            COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '24 hours') as kills_last_24h,
            
            -- Efficiency
            AVG(violation_score) as avg_violation_score
            
        FROM sentinel_kills
        WHERE weapon_class IS NOT NULL
        GROUP BY weapon_category, weapon_class, damage_type
        ORDER BY total_kills DESC
        """,
        
        # 3. PvP Hotspots
        """
        CREATE OR REPLACE VIEW sentinel_pvp_hotspots AS
        SELECT 
            grid_x,
            grid_y,
            
            -- Kill Stats
            COUNT(*) as kill_count,
            COUNT(DISTINCT killer_id) as unique_killers,
            COUNT(DISTINCT victim_id) as unique_victims,
            
            -- Distance Stats
            AVG(distance) as avg_distance,
            MAX(distance) as max_distance,
            
            -- Weapon Stats
            array_agg(DISTINCT weapon_category) as weapons_used,
            MODE() WITHIN GROUP (ORDER BY weapon_category) as most_used_weapon_category,
            
            -- Time Distribution
            COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 0 AND 6) as night_kills,
            COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 6 AND 18) as day_kills,
            
            -- Recent Activity
            MAX(timestamp) as last_kill_time,
            COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '7 days') as kills_last_7d
            
        FROM sentinel_kills
        WHERE victim_is_npc = FALSE
          AND killer_is_npc = FALSE
          AND grid_x IS NOT NULL
          AND grid_y IS NOT NULL
        GROUP BY grid_x, grid_y
        HAVING COUNT(*) > 5
        ORDER BY kill_count DESC
        """,
        
        # 4. NPC Kill Stats
        """
        CREATE OR REPLACE VIEW sentinel_npc_kill_stats AS
        SELECT 
            victim_npc_type,
            
            -- Kill Stats
            COUNT(*) as total_kills,
            COUNT(DISTINCT killer_id) as unique_killers,
            
            -- Top Killers
            MODE() WITHIN GROUP (ORDER BY killer_name) as top_killer_name,
            
            -- Weapon Stats
            MODE() WITHIN GROUP (ORDER BY weapon_category) as most_used_weapon,
            
            -- Distance Stats
            AVG(distance) as avg_distance,
            
            -- Recent Activity
            COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '7 days') as kills_last_7d,
            MAX(timestamp) as last_kill_time
            
        FROM sentinel_kills
        WHERE victim_is_npc = TRUE
          AND victim_npc_type IS NOT NULL
        GROUP BY victim_npc_type
        ORDER BY total_kills DESC
        """
    ]
    
    view_names = [
        "sentinel_player_kill_stats",
        "sentinel_weapon_meta",
        "sentinel_pvp_hotspots",
        "sentinel_npc_kill_stats"
    ]
    
    async with AsyncSession(engine) as session:
        print("🚀 Criando views de análise de killfeeds...\n")
        
        for idx, (sql, name) in enumerate(zip(views, view_names), 1):
            try:
                await session.execute(text(sql))
                await session.commit()
                print(f"  ✅ [{idx}/4] {name}")
            except Exception as e:
                await session.rollback()
                print(f"  ⚠️  [{idx}/4] {name} - Erro: {str(e)[:80]}")
        
        print("\n✅ Views criadas com sucesso!")
        print("\n📊 Views disponíveis:")
        print("  - sentinel_player_kill_stats (estatísticas por jogador)")
        print("  - sentinel_weapon_meta (análise de armas)")
        print("  - sentinel_pvp_hotspots (áreas quentes de PvP)")
        print("  - sentinel_npc_kill_stats (estatísticas de NPCs)")

if __name__ == "__main__":
    asyncio.run(create_kill_views())
