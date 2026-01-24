import asyncio
from app.core.database import engine
from sqlalchemy import text

async def update_view():
    async with engine.begin() as conn:
        print("Dropping old view...")
        await conn.execute(text("DROP VIEW IF EXISTS sentinel_player_ranks"))
        
        print("Creating new view...")
        await conn.execute(text("""
            CREATE VIEW sentinel_player_ranks AS
            WITH kills AS (
                SELECT 
                    killer_id, 
                    MAX(killer_name) as last_known_name,
                    COUNT(*) as kill_count
                FROM sentinel_kills
                WHERE killer_is_npc = FALSE AND victim_is_npc = FALSE
                GROUP BY killer_id
            ),
            deaths AS (
                SELECT 
                    victim_id, 
                    COUNT(*) as death_count
                FROM sentinel_kills
                WHERE victim_is_npc = FALSE AND killer_is_npc = FALSE
                GROUP BY victim_id
            )
            SELECT 
                COALESCE(r.current_name, k.last_known_name, 'Unknown') as player_name,
                COALESCE(k.kill_count, 0) as kills,
                COALESCE(d.death_count, 0) as deaths,
                CASE 
                    WHEN COALESCE(d.death_count, 0) = 0 THEN COALESCE(k.kill_count, 0)::float
                    ELSE COALESCE(k.kill_count, 0)::float / COALESCE(d.death_count, 0)::float
                END as kd_ratio,
                COALESCE(k.killer_id, d.victim_id) as steam_id
            FROM kills k
            FULL JOIN deaths d ON k.killer_id = d.victim_id
            LEFT JOIN sentinel_players_registry r ON COALESCE(k.killer_id, d.victim_id) = r.steam_id
            WHERE COALESCE(k.kill_count, 0) > 0 OR COALESCE(d.death_count, 0) > 0
            ORDER BY kd_ratio DESC, kills DESC;
        """))
        print("View updated successfully.")

if __name__ == "__main__":
    asyncio.run(update_view())
