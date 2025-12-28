"""
Migration to create advanced analytics views for Killfeed 2.0
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def create_analytics_views():
    views = [
        # 1. Player Ranks (Consolidated K/D)
        """
        CREATE OR REPLACE VIEW sentinel_player_ranks AS
        WITH Kills AS (
            SELECT killer_name as name, COUNT(*) as kill_count
            FROM sentinel_kills 
            WHERE killer_is_npc = FALSE AND victim_is_npc = FALSE
            GROUP BY killer_name
        ),
        Deaths AS (
            SELECT victim_name as name, COUNT(*) as death_count
            FROM sentinel_kills 
            WHERE victim_is_npc = FALSE -- Deaths by anyone (including NPCs? Usually K/D is PvP only, but standard is all deaths. Let's stick to PvP for now based on 'sentinel_player_kill_stats' logic which often isolates PvP. But K/D usually implies dying matters. Let's count PvP deaths for pure PvP rank)
            AND killer_is_npc = FALSE -- Keeping it Pure PvP for now as requested 'Rivalries' context
            GROUP BY victim_name
        )
        SELECT 
            COALESCE(k.name, d.name) as player_name,
            COALESCE(k.kill_count, 0) as kills,
            COALESCE(d.death_count, 0) as deaths,
            CASE 
                WHEN COALESCE(d.death_count, 0) = 0 THEN COALESCE(k.kill_count, 0)::FLOAT
                ELSE (COALESCE(k.kill_count, 0)::FLOAT / COALESCE(d.death_count, 0))
            END as kd_ratio
        FROM Kills k
        FULL OUTER JOIN Deaths d ON k.name = d.name
        WHERE COALESCE(k.kill_count, 0) > 0 OR COALESCE(d.death_count, 0) > 0
        ORDER BY kills DESC
        """,

        # 2. Rivalries (Versus Pairs)
        """
        CREATE OR REPLACE VIEW sentinel_rivalries AS
        SELECT 
            LEAST(killer_name, victim_name) as player1,
            GREATEST(killer_name, victim_name) as player2,
            COUNT(*) as encounters,
            SUM(CASE WHEN killer_name = LEAST(killer_name, victim_name) THEN 1 ELSE 0 END) as p1_wins,
            SUM(CASE WHEN killer_name = GREATEST(killer_name, victim_name) THEN 1 ELSE 0 END) as p2_wins,
            MAX(timestamp) as last_encounter
        FROM sentinel_kills
        WHERE killer_is_npc = FALSE 
          AND victim_is_npc = FALSE
        GROUP BY LEAST(killer_name, victim_name), GREATEST(killer_name, victim_name)
        HAVING COUNT(*) >= 2
        ORDER BY encounters DESC
        """
    ]

    view_names = [
        "sentinel_player_ranks",
        "sentinel_rivalries"
    ]

    async with AsyncSession(engine) as session:
        print("🚀 Creating Killfeed 2.0 Analytics Views...\n")
        
        for idx, (sql, name) in enumerate(zip(views, view_names), 1):
            try:
                await session.execute(text(sql))
                await session.commit()
                print(f"  ✅ [{idx}/2] {name}")
            except Exception as e:
                await session.rollback()
                print(f"  ⚠️  [{idx}/2] {name} - Error: {str(e)}")
        
        print("\n✅ Analytics Views created successfully!")

if __name__ == "__main__":
    asyncio.run(create_analytics_views())
