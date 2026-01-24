import asyncio
from app.core.database import engine
from sqlalchemy import text

async def update_clan_view():
    async with engine.begin() as conn:
        print("Dropping old view sentinel_clan_ranks...")
        await conn.execute(text("DROP VIEW IF EXISTS sentinel_clan_ranks"))
        
        print("Creating new view sentinel_clan_ranks...")
        await conn.execute(text("""
            CREATE VIEW sentinel_clan_ranks AS
            WITH clan_kills AS (
                SELECT 
                    r.squad_name,
                    COUNT(*) as kill_count,
                    MAX(k.distance) as max_distance
                FROM sentinel_kills k
                JOIN sentinel_players_registry r ON k.killer_id = r.steam_id
                WHERE k.killer_is_npc = FALSE 
                  AND k.victim_is_npc = FALSE
                  AND r.squad_name IS NOT NULL
                  AND r.squad_name != ''
                GROUP BY r.squad_name
            ),
            clan_deaths AS (
                SELECT 
                    r.squad_name,
                    COUNT(*) as death_count
                FROM sentinel_kills k
                JOIN sentinel_players_registry r ON k.victim_id = r.steam_id
                WHERE k.victim_is_npc = FALSE 
                  AND k.killer_is_npc = FALSE
                  AND r.squad_name IS NOT NULL
                  AND r.squad_name != ''
                GROUP BY r.squad_name
            )
            SELECT 
                COALESCE(ck.squad_name, cd.squad_name) as squad_name,
                COALESCE(ck.kill_count, 0) as kills,
                COALESCE(cd.death_count, 0) as deaths,
                COALESCE(ck.max_distance, 0) as longest_shot,
                CASE 
                    WHEN COALESCE(cd.death_count, 0) = 0 THEN COALESCE(ck.kill_count, 0)::float
                    ELSE COALESCE(ck.kill_count, 0)::float / COALESCE(cd.death_count, 0)::float
                END as kd_ratio
            FROM clan_kills ck
            FULL JOIN clan_deaths cd ON ck.squad_name = cd.squad_name
            WHERE COALESCE(ck.kill_count, 0) > 0 OR COALESCE(cd.death_count, 0) > 0
            ORDER BY kd_ratio DESC, kills DESC;
        """))
        print("View sentinel_clan_ranks updated successfully.")

if __name__ == "__main__":
    asyncio.run(update_clan_view())
