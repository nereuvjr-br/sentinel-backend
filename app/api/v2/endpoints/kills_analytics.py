"""
Kills Analytics API - Enhanced Endpoints
Endpoints aprimorados para análise de killfeeds
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlmodel import select
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.kill_v2 import SentinelKill
from datetime import datetime, timedelta
from typing import List, Optional

router = APIRouter()

# ============================================================================
# PLAYER KILL STATS (View)
# ============================================================================

@router.get("/stats/players")
async def get_player_kill_stats(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    min_kills: Optional[int] = None
):
    """
    Estatísticas de kills por jogador (view sentinel_player_kill_stats).
    """
    query = """
        SELECT * FROM sentinel_player_kill_stats
        WHERE 1=1
    """
    params = {}
    
    if search:
        query += " AND killer_name ILIKE :search"
        params["search"] = f"%{search}%"
    
    if min_kills:
        query += " AND total_kills >= :min_kills"
        params["min_kills"] = min_kills
    
    query += " ORDER BY total_kills DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    
    result = await session.execute(text(query), params)
    rows = result.fetchall()
    
    return [
        {
            "killer_id": row[0],
            "killer_name": row[1],
            "total_kills": row[2],
            "player_kills": row[3],
            "npc_kills": row[4],
            "weapon_categories_used": row[5],
            "favorite_weapon_category": row[6],
            "favorite_weapon": row[7],
            "avg_kill_distance": float(row[8]) if row[8] else 0,
            "longest_kill": float(row[9]) if row[9] else 0,
            "shortest_kill": float(row[10]) if row[10] else 0,
            "night_kills": row[11],
            "day_kills": row[12],
            "evening_kills": row[13],
            "avg_violation_score": float(row[14]) if row[14] else 0,
            "max_violation_score": float(row[15]) if row[15] else 0,
            "first_kill": row[16].isoformat() if row[16] else None,
            "last_kill": row[17].isoformat() if row[17] else None
        }
        for row in rows
    ]


@router.get("/stats/players/{steam_id}")
async def get_player_kill_stats_detail(
    steam_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Estatísticas detalhadas de um jogador específico.
    """
    query = text("""
        SELECT * FROM sentinel_player_kill_stats
        WHERE killer_id = :steam_id
    """)
    
    result = await session.execute(query, {"steam_id": steam_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    
    return {
        "killer_id": row[0],
        "killer_name": row[1],
        "total_kills": row[2],
        "player_kills": row[3],
        "npc_kills": row[4],
        "weapon_categories_used": row[5],
        "favorite_weapon_category": row[6],
        "favorite_weapon": row[7],
        "avg_kill_distance": float(row[8]) if row[8] else 0,
        "longest_kill": float(row[9]) if row[9] else 0,
        "shortest_kill": float(row[10]) if row[10] else 0,
        "night_kills": row[11],
        "day_kills": row[12],
        "evening_kills": row[13],
        "avg_violation_score": float(row[14]) if row[14] else 0,
        "max_violation_score": float(row[15]) if row[15] else 0,
        "first_kill": row[16].isoformat() if row[16] else None,
        "last_kill": row[17].isoformat() if row[17] else None
    }


# ============================================================================
# WEAPON META (View)
# ============================================================================

@router.get("/stats/weapons")
async def get_weapon_meta(
    session: AsyncSession = Depends(get_session),
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(50, le=500),
    weapon_category: Optional[str] = None
):
    """
    Análise de meta de armas (Dinâmico com filtro de data).
    Substitui a view estática para permitir time ranges.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Base Filters
    filters = ["k.timestamp >= :start_date", "k.is_event = FALSE"]
    
    if weapon_category:
        filters.append("k.weapon_category = :category")

    where_clause = " AND ".join(filters)

    query = text(f"""
        SELECT 
            k.weapon_category,
            k.weapon_class,
            k.damage_type,
            COUNT(*) as total_kills,
            COUNT(DISTINCT k.killer_id) as unique_users,
            AVG(k.distance) as avg_kill_distance,
            MAX(k.distance) as max_kill_distance,
            SUM(CASE WHEN k.victim_is_npc = FALSE AND k.killer_is_npc = FALSE THEN 1 ELSE 0 END) as pvp_kills,
            SUM(CASE WHEN k.victim_is_npc = TRUE THEN 1 ELSE 0 END) as pve_kills
        FROM sentinel_kills k
        WHERE {where_clause}
          AND k.weapon_class IS NOT NULL 
          AND k.weapon_class != ''
        GROUP BY k.weapon_category, k.weapon_class, k.damage_type
        ORDER BY total_kills DESC
        LIMIT :limit
    """)
    
    params = {"start_date": start_date, "limit": limit}
    if weapon_category:
        params["category"] = weapon_category
        
    result = await session.execute(query, params)
    rows = result.fetchall()
    
    return [
        {
            "weapon_category": row[0],
            "weapon_class": row[1],
            "damage_type": row[2],
            "total_kills": row[3],
            "unique_users": row[4],
            "avg_kill_distance": float(row[5]) if row[5] else 0,
            "max_kill_distance": float(row[6]) if row[6] else 0,
            "pvp_kills": row[7],
            "pve_kills": row[8]
        }
        for row in rows
    ]


@router.get("/stats/weapons/categories")
async def get_weapon_categories_summary(
    session: AsyncSession = Depends(get_session)
):
    """
    Resumo por categoria de arma.
    """
    query = text("""
        SELECT 
            weapon_category,
            SUM(total_kills) as total_kills,
            SUM(pvp_kills) as pvp_kills,
            SUM(pve_kills) as pve_kills,
            AVG(avg_kill_distance) as avg_distance,
            COUNT(DISTINCT weapon_class) as weapons_in_category
        FROM sentinel_weapon_meta
        GROUP BY weapon_category
        ORDER BY total_kills DESC
    """)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    return [
        {
            "weapon_category": row[0],
            "total_kills": row[1],
            "pvp_kills": row[2],
            "pve_kills": row[3],
            "avg_distance": float(row[4]) if row[4] else 0,
            "weapons_in_category": row[5]
        }
        for row in rows
    ]




# ============================================================================
# NPC STATS (View)
# ============================================================================

@router.get("/stats/npcs")
async def get_npc_stats(
    session: AsyncSession = Depends(get_session)
):
    """
    Estatísticas de kills de NPCs (view sentinel_npc_kill_stats).
    """
    query = text("""
        SELECT * FROM sentinel_npc_kill_stats
        ORDER BY total_kills DESC
    """)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    return [
        {
            "victim_npc_type": row[0],
            "total_kills": row[1],
            "unique_killers": row[2],
            "top_killer_name": row[3],
            "most_used_weapon": row[4],
            "avg_distance": float(row[5]) if row[5] else 0,
            "kills_last_7d": row[6],
            "last_kill_time": row[7].isoformat() if row[7] else None
        }
        for row in rows
    ]


# ============================================================================
# LEADERBOARDS
# ============================================================================

@router.get("/leaderboard/pvp")
async def get_pvp_leaderboard(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(20, le=100),
    hours: Optional[int] = None
):
    """
    Leaderboard de PvP (jogadores com mais kills de players).
    Grouped strictly by SteamID. Name fetched from Registry.
    """
    base_query = """
        SELECT 
            k.killer_id,
            COALESCE(MAX(r.current_name), MAX(k.killer_name)) as killer_name,
            COUNT(*) as kills,
            AVG(k.distance) as avg_distance,
            MAX(k.distance) as longest_kill
        FROM sentinel_kills k
        LEFT JOIN sentinel_players_registry r ON k.killer_id = r.steam_id
        WHERE k.victim_is_npc = FALSE
          AND k.killer_is_npc = FALSE
          AND k.is_event = FALSE

    """
    params = {"limit": limit}
    
    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        base_query += " AND k.timestamp >= :cutoff"
        params["cutoff"] = cutoff
    
    base_query += """
        GROUP BY k.killer_id
        ORDER BY kills DESC
        LIMIT :limit
    """
    
    result = await session.execute(text(base_query), params)
    rows = result.fetchall()
    
    return [
        {
            "rank": idx + 1,
            "killer_id": row[0],
            "killer_name": row[1],
            "kills": row[2],
            "avg_distance": float(row[3]) if row[3] else 0,
            "longest_kill": float(row[4]) if row[4] else 0
        }
        for idx, row in enumerate(rows)
    ]


@router.get("/leaderboard/distance")
async def get_distance_leaderboard(
    session: AsyncSession = Depends(get_session),
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(20, le=100)
):
    """
    Leaderboard de longest kills (com filtro de data).
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    query = text("""
        SELECT 
            k.killer_id,
            COALESCE(r.current_name, k.killer_name) as killer_name,
            k.victim_name,
            k.weapon_category,
            k.weapon_class,
            k.distance,
            k.timestamp
        FROM sentinel_kills k
        LEFT JOIN sentinel_players_registry r ON k.killer_id = r.steam_id
        WHERE k.distance > 50
          AND k.timestamp >= :start_date
          AND k.victim_is_npc = FALSE
          AND k.killer_is_npc = FALSE
          AND k.is_event = FALSE

          AND k.weapon_class NOT ILIKE '%Bleeding%'
          AND k.weapon_class NOT ILIKE '%Injury%'
          AND k.weapon_class NOT ILIKE '%Environment%'
          AND k.weapon_class NOT ILIKE '%Trap%'
          AND k.weapon_class NOT ILIKE '%Melee%'
          AND k.weapon_class NOT ILIKE '%Unarmed%'
          AND k.weapon_class NOT ILIKE '%Mine%'
          AND k.weapon_class NOT ILIKE '%C4%'
          AND k.weapon_class NOT ILIKE '%Claymore%'
          AND k.weapon_class NOT ILIKE '%Explosive%'
          AND k.weapon_class IS NOT NULL 
          AND k.weapon_class != ''
          AND k.weapon_class != 'Unknown'
        ORDER BY k.distance DESC
        LIMIT :limit
    """)
    
    result = await session.execute(query, {"limit": limit, "start_date": start_date})
    rows = result.fetchall()
    
    return [
        {
            "rank": idx + 1,
            "killer_id": row[0],
            "killer_name": row[1],
            "victim_name": row[2],
            "weapon_category": row[3],
            "weapon_class": row[4],
            "distance": float(row[5]) if row[5] else 0,
            "timestamp": row[6].isoformat() if row[6] else None
        }
        for idx, row in enumerate(rows)
    ]


@router.get("/leaderboard/weapon/{weapon_category}")
async def get_weapon_leaderboard(
    weapon_category: str,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(20, le=100)
):
    """
    Leaderboard por categoria de arma.
    """
    query = text("""
        SELECT 
            k.killer_id,
            COALESCE(MAX(r.current_name), MAX(k.killer_name)) as killer_name,
            COUNT(*) as kills,
            AVG(k.distance) as avg_distance
        FROM sentinel_kills k
        LEFT JOIN sentinel_players_registry r ON k.killer_id = r.steam_id
        WHERE k.weapon_category = :category
          AND k.victim_is_npc = FALSE
          AND k.is_event = FALSE

        GROUP BY k.killer_id
        ORDER BY kills DESC
        LIMIT :limit
    """)
    
    result = await session.execute(query, {"category": weapon_category, "limit": limit})
    rows = result.fetchall()
    
    return [
        {
            "rank": idx + 1,
            "killer_id": row[0],
            "killer_name": row[1],
            "kills": row[2],
            "avg_distance": float(row[3]) if row[3] else 0
        }
        for idx, row in enumerate(rows)
    ]


# ============================================================================
# RECENT KILLS (Enhanced)
# ============================================================================

@router.get("/recent")
async def get_recent_kills(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=200),
    weapon_category: Optional[str] = None,
    damage_type: Optional[str] = None,
    killer_is_npc: Optional[bool] = None,
    victim_is_npc: Optional[bool] = None,
    min_distance: Optional[float] = None,
    grid_x: Optional[int] = None,
    grid_y: Optional[int] = None
):
    """
    Kills recentes com filtros aprimorados.
    """
    statement = select(SentinelKill)
    
    if weapon_category:
        statement = statement.where(SentinelKill.weapon_category == weapon_category)
    
    if damage_type:
        statement = statement.where(SentinelKill.damage_type == damage_type)
    
    if killer_is_npc is not None:
        statement = statement.where(SentinelKill.killer_is_npc == killer_is_npc)
    
    if victim_is_npc is not None:
        statement = statement.where(SentinelKill.victim_is_npc == victim_is_npc)
    
    if min_distance:
        statement = statement.where(SentinelKill.distance >= min_distance)
    
    if grid_x is not None:
        statement = statement.where(SentinelKill.grid_x == grid_x)
    
    if grid_y is not None:
        statement = statement.where(SentinelKill.grid_y == grid_y)
    
    # Always exclude events
    statement = statement.where(SentinelKill.is_event == False)

    
    statement = statement.order_by(SentinelKill.timestamp.desc()).limit(limit)
    
    
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/stats/pve/victims")
async def get_top_pve_victims(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(10, le=50)
):
    """
    Jogadores que mais morreram para NPCs.
    """
    query = text("""
        SELECT victim_name, COUNT(*) as death_count
        FROM sentinel_kills
        WHERE killer_is_npc = TRUE AND victim_is_npc = FALSE
        GROUP BY victim_name
        ORDER BY death_count DESC
        LIMIT :limit
    """)
    result = await session.execute(query, {"limit": limit})
    rows = result.fetchall()
    return [{"name": row[0], "count": row[1]} for row in rows]

# ============================================================================
# GLOBAL STATS
# ============================================================================

@router.get("/stats/global")
async def get_global_stats(
    session: AsyncSession = Depends(get_session),
    hours: Optional[int] = Query(None, description="Filter by last X hours")
):
    """
    Estatísticas globais do servidor.
    Se 'hours' for fornecido, filtra apenas dados recentes.
    """
    params = {}
    time_filter = ""
    
    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        time_filter = "WHERE timestamp >= :cutoff"
        params["cutoff"] = cutoff
    
    # Helper to append filters safely
    def build_query(base_query, is_filtered=False):
        if not hours:
            return text(base_query)
        
        # Se a query base já tem WHERE, usamos AND. Se não, usamos WHERE.
        # As queries abaixo tem estruturas especificas.
        
        # Query 1: Total Kills
        # SELECT COUNT(*) FROM sentinel_kills [WHERE ...]
        
        # Query 2: Unique Players
        # SELECT COUNT(DISTINCT killer_id) FROM sentinel_kills [WHERE ...]
        
        # Queries 3 & 4 (Avg/Max Dist) já tem WHERE clauses complexas.
        # Precisamos adicionar AND timestamp >= :cutoff
        pass

    # Total Kills (PvP Only - Strict Filters)
    # Exclude:
    # 1. Victim is NPC
    # 2. Killer is NPC flag (legacy)
    # 3. Killer Name starts with BP_ (Drifters, Guards)
    # 4. Killer Name is 'Unknown' (System errors/Environment)
    # 5. Killer ID is too short OR contains -1 (Environment/Mines)
    # 6. Killer ID equals Victim ID (Suicides)
    # 7. Events (Deathmatch/Minigames)
    base_filters = """
        WHERE victim_is_npc = FALSE 
          AND killer_is_npc = FALSE
          AND killer_name NOT LIKE 'BP_%'
          AND killer_name != 'Unknown'
          AND killer_id NOT LIKE '%-1%'
          AND LENGTH(killer_id) > 5
          AND killer_id != victim_id
          AND is_event = FALSE
    """
    
    if hours:
        q_total = f"SELECT COUNT(*) FROM sentinel_kills {base_filters} AND timestamp >= :cutoff"
    else:
        q_total = f"SELECT COUNT(*) FROM sentinel_kills {base_filters}"
        
    total_kills = (await session.execute(text(q_total), params)).scalar() or 0

    # Unique Killers (Active Combatants)
    q_unique = f"SELECT COUNT(DISTINCT killer_id) FROM sentinel_kills {base_filters}"
    if hours:
        q_unique += " AND timestamp >= :cutoff"
    unique_players = (await session.execute(text(q_unique), params)).scalar() or 0

    # Base filters for Distance queries
    dist_filters = """
        WHERE distance > 0 
          AND victim_is_npc = FALSE
          AND killer_is_npc = FALSE
          AND weapon_class NOT ILIKE '%Melee%' 
          AND weapon_class NOT ILIKE '%Unarmed%'
          AND weapon_class NOT ILIKE '%Environment%'
          AND weapon_class NOT ILIKE '%Suicide%'
          AND weapon_class NOT ILIKE '%Trap%'
          AND weapon_class NOT ILIKE '%Bleeding%'
          AND weapon_class NOT ILIKE '%Injury%'
          AND weapon_class NOT ILIKE '%Mine%'
          AND weapon_class NOT ILIKE '%C4%'
          AND weapon_class NOT ILIKE '%Claymore%'
          AND weapon_class NOT ILIKE '%Explosive%'
          AND weapon_class IS NOT NULL 
          AND weapon_class != ''
          AND weapon_class != 'Unknown'
    """
    
    if hours:
        dist_filters += " AND timestamp >= :cutoff"

    # Avg Distance
    avg_dist_query = f"SELECT AVG(distance) FROM sentinel_kills {dist_filters}"
    avg_dist = (await session.execute(text(avg_dist_query), params)).scalar() or 0

    # Max Distance
    max_dist_query = f"SELECT MAX(distance) FROM sentinel_kills {dist_filters}"
    max_dist = (await session.execute(text(max_dist_query), params)).scalar() or 0

    return {
        "totalKills": total_kills,
        "uniquePlayers": unique_players, # In time window context, this is "Active Players"
        "avgDistance": float(avg_dist),
        "maxDistance": float(max_dist)
    }

# ============================================================================
# ANALYTICS 2.0 (New Endpoints)
# ============================================================================

@router.get("/analytics/rankings")
async def get_consolidated_rankings(
    session: AsyncSession = Depends(get_session),
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(50, le=200),
    min_kills: int = Query(5),
    sort_by: str = Query("kd", regex="^(kd|kills)$")
):
    """
    Rankings consolidados (K/D Real).
    Calculado dinamicamente com filtro de período (default 7 dias).
    sort_by: 'kd' (default) ou 'kills'.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Common filters
    filters = """
        timestamp >= :start_date 
        AND victim_is_npc = FALSE 
        AND is_event = FALSE
    """
    
    order_clause = "kd_ratio DESC, kills DESC"
    if sort_by == "kills":
        order_clause = "kills DESC, kd_ratio DESC"
        
    query = text(f"""
        WITH kill_counts AS (
            SELECT killer_id, COUNT(*) as kills, MAX(distance) as longest_shot
            FROM sentinel_kills
            WHERE {filters} AND killer_is_npc = FALSE
            GROUP BY killer_id
        ),
        death_counts AS (
            SELECT victim_id, COUNT(*) as deaths
            FROM sentinel_kills
            WHERE {filters}
            GROUP BY victim_id
        )
        SELECT 
            COALESCE(r.current_name, 'Unknown') as player_name,
            COALESCE(kc.kills, 0) as kills,
            COALESCE(dc.deaths, 0) as deaths,
            CASE 
                WHEN COALESCE(dc.deaths, 0) = 0 THEN COALESCE(kc.kills, 0)
                ELSE CAST(COALESCE(kc.kills, 0) AS FLOAT) / dc.deaths
            END as kd_ratio,
            kc.longest_shot
        FROM kill_counts kc
        LEFT JOIN death_counts dc ON kc.killer_id = dc.victim_id
        LEFT JOIN sentinel_players_registry r ON kc.killer_id = r.steam_id
        WHERE COALESCE(kc.kills, 0) >= :min_kills
        ORDER BY {order_clause}
        LIMIT :limit
    """)
    
    result = await session.execute(query, {"min_kills": min_kills, "limit": limit, "start_date": start_date})
    rows = result.fetchall()
    
    return [
        {
            "rank": idx + 1,
            "name": row[0],
            "count": row[1], # kills
            "deaths": row[2],
            "kd": float(row[3]),
            "steamId": row[4]
        }
        for idx, row in enumerate(rows)
    ]


@router.get("/analytics/rankings/clans")
async def get_clan_rankings(
    session: AsyncSession = Depends(get_session),
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(50, le=200),
    min_kills: int = Query(0),
    sort_by: str = Query("kd", regex="^(kd|kills|traps)$")
):
    """
    Rankings de Clãs (K/D, Kills e Traps).
    Calculado dinamicamente com filtro de período.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Base filter for valid combat kills/deaths
    valid_kill_filter = """
        k.victim_is_npc = FALSE 
        AND k.killer_is_npc = FALSE
        AND k.is_event = FALSE
        AND k.timestamp >= :start_date
    """
    
    # Filter for TRAPS
    trap_filter = """
        k.victim_is_npc = FALSE
        AND k.killer_is_npc = FALSE
        AND k.is_event = FALSE
        AND k.timestamp >= :start_date
        AND (
            k.weapon_class ILIKE '%Trap%' OR
            k.weapon_class ILIKE '%Mine%' OR
            k.weapon_class ILIKE '%Claymore%' OR
            k.weapon_class ILIKE '%C4%'
        )
    """

    order_clause = "kd_ratio DESC, kills DESC"
    if sort_by == "kills":
        order_clause = "kills DESC, kd_ratio DESC"
    elif sort_by == "traps":
        order_clause = "trap_kills DESC"

    query = text(f"""
        WITH clan_kills AS (
            SELECT 
                r.squad_name, 
                COUNT(*) as kills
            FROM sentinel_kills k
            JOIN sentinel_players_registry r ON k.killer_id = r.steam_id
            WHERE {valid_kill_filter}
              AND r.squad_name IS NOT NULL 
              AND r.squad_name != '' 
              AND r.squad_name != 'No Squad'
            GROUP BY r.squad_name
        ),
        clan_deaths AS (
            SELECT 
                r.squad_name, 
                COUNT(*) as deaths
            FROM sentinel_kills k
            JOIN sentinel_players_registry r ON k.victim_id = r.steam_id
            WHERE {valid_kill_filter}
              AND r.squad_name IS NOT NULL 
              AND r.squad_name != '' 
              AND r.squad_name != 'No Squad'
            GROUP BY r.squad_name
        ),
        clan_traps AS (
            SELECT 
                r.squad_name, 
                COUNT(*) as trap_kills
            FROM sentinel_kills k
            JOIN sentinel_players_registry r ON k.killer_id = r.steam_id
            WHERE {trap_filter}
              AND r.squad_name IS NOT NULL 
              AND r.squad_name != '' 
              AND r.squad_name != 'No Squad'
            GROUP BY r.squad_name
        )
        SELECT 
            ck.squad_name,
            COALESCE(ck.kills, 0) as kills,
            COALESCE(cd.deaths, 0) as deaths,
            CASE 
                WHEN COALESCE(cd.deaths, 0) = 0 THEN COALESCE(ck.kills, 0)
                ELSE CAST(COALESCE(ck.kills, 0) AS FLOAT) / cd.deaths
            END as kd_ratio,
            COALESCE(ct.trap_kills, 0) as trap_kills
        FROM clan_kills ck
        LEFT JOIN clan_deaths cd ON ck.squad_name = cd.squad_name
        LEFT JOIN clan_traps ct ON ck.squad_name = ct.squad_name
        WHERE COALESCE(ck.kills, 0) >= :min_kills
        ORDER BY {order_clause}
        LIMIT :limit
    """)
    
    result = await session.execute(query, {
        "min_kills": min_kills, 
        "limit": limit,
        "start_date": start_date
    })
    rows = result.fetchall()
    
    return [
        {
            "rank": idx + 1,
            "name": row.squad_name,
            "count": row.kills,
            "deaths": row.deaths,
            "kd": float(row.kd_ratio),
            "traps": int(row.trap_kills)
        }
        for idx, row in enumerate(rows)
    ]

@router.get("/analytics/rivalries")
async def get_top_rivalries(
    session: AsyncSession = Depends(get_session),
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(10, le=50)
):
    """
    Top rivalidades de Jogadores (Dynamically calculated).
    Default: Last 7 days.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = text("""
        SELECT 
            LEAST(k.killer_name, k.victim_name) as p1,
            GREATEST(k.killer_name, k.victim_name) as p2,
            COUNT(*) as encounters,
            SUM(CASE WHEN k.killer_name = LEAST(k.killer_name, k.victim_name) THEN 1 ELSE 0 END) as p1_wins,
            SUM(CASE WHEN k.killer_name = GREATEST(k.killer_name, k.victim_name) THEN 1 ELSE 0 END) as p2_wins,
            MAX(k.timestamp) as last_encounter
        FROM sentinel_kills k
        WHERE k.timestamp >= :start_date
          AND k.victim_is_npc = FALSE 
          AND k.killer_is_npc = FALSE
          AND k.is_event = FALSE

          AND k.killer_name IS NOT NULL AND k.victim_name IS NOT NULL
          AND k.killer_name != 'Unknown' AND k.victim_name != 'Unknown'
        GROUP BY p1, p2
        ORDER BY encounters DESC
        LIMIT :limit
    """)
    
    result = await session.execute(query, {"start_date": start_date, "limit": limit})
    rows = result.fetchall()
    
    return [
        {
            "player1": row[0],
            "player2": row[1],
            "encounters": row[2],
            "p1Wins": row[3],
            "p2Wins": row[4],
            "winner": row[0] if row[3] > row[4] else (row[1] if row[4] > row[3] else "Draw"),
            "last_encounter": row[5]
        }
        for row in rows
    ]

@router.get("/analytics/versus")
async def get_versus_history(
    player1: str,
    player2: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """
    Histórico detalhado entre dois jogadores.
    """
    filters = [
        ((SentinelKill.killer_name == player1) & (SentinelKill.victim_name == player2)) |
        ((SentinelKill.killer_name == player2) & (SentinelKill.victim_name == player1)),
        SentinelKill.is_event == False
    ]

    
    if start_date:
        filters.append(SentinelKill.timestamp >= start_date)
    if end_date:
        filters.append(SentinelKill.timestamp <= end_date)
        
    query = select(SentinelKill).where(*filters).order_by(SentinelKill.timestamp.desc())
    
    result = await session.execute(query)
    logs = result.scalars().all()
    
    score_p1 = sum(1 for log in logs if log.killer_name == player1)
    score_p2 = sum(1 for log in logs if log.killer_name == player2)
    
    return {
        "player1": player1,
        "player2": player2,
        "totalEncounters": len(logs),
        "scoreP1": score_p1,
        "scoreP2": score_p2,
        "history": logs
    }


@router.get("/analytics/versus/clans")
async def get_clan_versus_history(
    clan1: str,
    clan2: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """
    Histórico detalhado entre dois Clãs.
    """
    from app.models.players_registry_v2 import SentinelPlayerRegistry
    from sqlalchemy.orm import aliased
    
    # Aliases para self-join do registry
    KillerReg = aliased(SentinelPlayerRegistry)
    VictimReg = aliased(SentinelPlayerRegistry)
    
    params = {"clan1": clan1, "clan2": clan2}
    
    # Base Query
    query_text = """
        SELECT 
            k.*,
            kr.squad_name as killer_clan,
            vr.squad_name as victim_clan
        FROM sentinel_kills k
        JOIN sentinel_players_registry kr ON k.killer_id = kr.steam_id
        JOIN sentinel_players_registry vr ON k.victim_id = vr.steam_id
        WHERE 
            k.is_event = FALSE AND
            (
                (kr.squad_name = :clan1 AND vr.squad_name = :clan2) 
                OR 
                (kr.squad_name = :clan2 AND vr.squad_name = :clan1)
            )
    """
    
    if start_date:
        query_text += " AND k.timestamp >= :start_date"
        params["start_date"] = start_date
        
    if end_date:
        query_text += " AND k.timestamp <= :end_date"
        params["end_date"] = end_date
        
    query_text += " ORDER BY k.timestamp DESC"
    
    result = await session.execute(text(query_text), params)
    rows = result.fetchall()
    
    # Process Results
    logs = []
    score_c1 = 0
    score_c2 = 0
    
    for row in rows:
        # Map row to simple object or model
        # Row structure: [k.id, k.timestamp, ..., k.processed_at, killer_clan, victim_clan]
        # SQLModel select usually returns model objects, but text returns tuples.
        # We need to reconstruct the log object essentially for the frontend.
        # However, frontend expects SentinelKill structure mostly.
        
        # Simplificação: Vamos construir um dict
        # Assuming SentinelKill columns order roughly, or just access by name if mapped (text result acts like named tuple usually)
        
        # Safe access by column name
        k_clan = row.killer_clan
        
        if k_clan == clan1:
            score_c1 += 1
        else:
            score_c2 += 1
            
        logs.append({
            "id": row.id,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "killer_name": row.killer_name,
            "victim_name": row.victim_name,
            "weapon": row.weapon,
            "distance": row.distance,
            "killer_clan": row.killer_clan,
            "victim_clan": row.victim_clan
        })
        
    return {
        "clan1": clan1,
        "clan2": clan2,
        "totalEncounters": len(logs),
        "scoreC1": score_c1,
        "scoreC2": score_c2,
        "history": logs
    }
        
@router.get("/analytics/clans/list")
async def get_clan_list(
    session: AsyncSession = Depends(get_session)
):
    """
    Lista simples de nomes de clãs para comboboxes.
    """
    from app.models.clan_v2 import SentinelClan
    
    query = select(SentinelClan.name).distinct().order_by(SentinelClan.name)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/analytics/players/list")
async def get_player_list(
    session: AsyncSession = Depends(get_session)
):
    """
    Lista simples de nomes de jogadores do Registry (SCUM.db) para comboboxes.
    """
    from app.models.players_registry_v2 import SentinelPlayerRegistry
    
    # Busca apenas nomes não nulos e ordena
    query = select(SentinelPlayerRegistry.current_name).where(SentinelPlayerRegistry.current_name != None).distinct().order_by(SentinelPlayerRegistry.current_name)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/analytics/rivalries/clans")
async def get_clan_rivalries(
    session: AsyncSession = Depends(get_session),
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(5, ge=1, le=20)
):
    """
    Rivalidades de Clãs (TOP 5 por padrão, últimos 7 dias).
    Agrupa encontros entre dois clãs e conta quem matou mais.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = text("""
        SELECT 
            LEAST(kr.squad_name, vr.squad_name) as clan_a,
            GREATEST(kr.squad_name, vr.squad_name) as clan_b,
            COUNT(*) as encounters,
            SUM(CASE WHEN kr.squad_name = LEAST(kr.squad_name, vr.squad_name) THEN 1 ELSE 0 END) as score_a,
            SUM(CASE WHEN kr.squad_name = GREATEST(kr.squad_name, vr.squad_name) THEN 1 ELSE 0 END) as score_b
        FROM sentinel_kills k
        JOIN sentinel_players_registry kr ON k.killer_id = kr.steam_id
        JOIN sentinel_players_registry vr ON k.victim_id = vr.steam_id
        WHERE k.timestamp >= :start_date
          AND kr.squad_name IS NOT NULL AND kr.squad_name != '' AND kr.squad_name != 'No Squad'
          AND vr.squad_name IS NOT NULL AND vr.squad_name != '' AND vr.squad_name != 'No Squad'
          AND kr.squad_name != vr.squad_name
          AND k.victim_is_npc = FALSE 
          AND k.killer_is_npc = FALSE
          AND k.is_event = FALSE
        GROUP BY clan_a, clan_b
        ORDER BY encounters DESC
        LIMIT :limit
    """)
    
    result = await session.execute(query, {"start_date": start_date, "limit": limit})
    rows = result.fetchall()
    
    return [
        {
            "clan1": row[0],
            "clan2": row[1],
            "encounters": row[2],
            "score1": row[3],
            "score2": row[4],
            "winner": row[0] if row[3] > row[4] else (row[1] if row[4] > row[3] else "Draw")
        }
        for row in rows
    ]
