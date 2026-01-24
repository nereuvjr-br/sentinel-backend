import asyncio
from app.core.database import engine
from sqlalchemy import text

async def fix_views():
    async with engine.begin() as conn:
        print("Dropping old view sentinel_player_kill_stats...")
        await conn.execute(text("DROP VIEW IF EXISTS sentinel_player_kill_stats"))
        
        print("Creating new view sentinel_player_kill_stats (GROUP BY ID ONLY)...")
        # Note: We now join with registry to get the canonical name. 
        # Fallback to MAX(killer_name) if not in registry.
        
        sql = """
            CREATE VIEW sentinel_player_kill_stats AS
            SELECT 
                k.killer_id,
                COALESCE(MAX(r.current_name), MAX(k.killer_name), 'Unknown') as killer_name,
                count(*) AS total_kills,
                count(*) FILTER (WHERE k.victim_is_npc = false) AS player_kills,
                count(*) FILTER (WHERE k.victim_is_npc = true) AS npc_kills,
                count(DISTINCT k.weapon_category) AS weapon_categories_used,
                mode() WITHIN GROUP (ORDER BY k.weapon_category) AS favorite_weapon_category,
                mode() WITHIN GROUP (ORDER BY k.weapon_class) AS favorite_weapon,
                avg(k.distance) AS avg_kill_distance,
                max(k.distance) AS longest_kill,
                min(k.distance) FILTER (WHERE k.distance > 0::double precision) AS shortest_kill,
                count(*) FILTER (WHERE EXTRACT(hour FROM k."timestamp") >= 0::numeric AND EXTRACT(hour FROM k."timestamp") <= 6::numeric) AS night_kills,
                count(*) FILTER (WHERE EXTRACT(hour FROM k."timestamp") >= 6::numeric AND EXTRACT(hour FROM k."timestamp") <= 18::numeric) AS day_kills,
                count(*) FILTER (WHERE EXTRACT(hour FROM k."timestamp") >= 18::numeric AND EXTRACT(hour FROM k."timestamp") <= 24::numeric) AS evening_kills,
                avg(k.violation_score) AS avg_violation_score,
                max(k.violation_score) AS max_violation_score,
                min(k."timestamp") AS first_kill,
                max(k."timestamp") AS last_kill,
                max(k."timestamp") - min(k."timestamp") AS active_period
            FROM sentinel_kills k
            LEFT JOIN sentinel_players_registry r ON k.killer_id = r.steam_id
            WHERE k.killer_id IS NOT NULL 
              AND k.killer_is_npc = false
            GROUP BY k.killer_id;
        """
        await conn.execute(text(sql))
        print("View sentinel_player_kill_stats updated successfully.")

if __name__ == "__main__":
    asyncio.run(fix_views())
