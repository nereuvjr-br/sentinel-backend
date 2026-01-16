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
    limit: int = Query(50, le=500),
    weapon_category: Optional[str] = None,
    damage_type: Optional[str] = None
):
    """
    Análise de meta de armas (view sentinel_weapon_meta).
    """
    query = """
        SELECT * FROM sentinel_weapon_meta
        WHERE 1=1
    """
    params = {}
    
    if weapon_category:
        query += " AND weapon_category = :category"
        params["category"] = weapon_category
    
    if damage_type:
        query += " AND damage_type = :damage_type"
        params["damage_type"] = damage_type
    
    query += " LIMIT :limit"
    params["limit"] = limit
    
    result = await session.execute(text(query), params)
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
            "pve_kills": row[8],
            "kills_last_7d": row[9],
            "kills_last_24h": row[10],
            "avg_violation_score": float(row[11]) if row[11] else 0
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
    """
    query = """
        SELECT 
            killer_id,
            killer_name,
            COUNT(*) as kills,
            AVG(distance) as avg_distance,
            MAX(distance) as longest_kill
        FROM sentinel_kills
        WHERE victim_is_npc = FALSE
          AND killer_is_npc = FALSE
    """
    params = {"limit": limit}
    
    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query += " AND timestamp >= :cutoff"
        params["cutoff"] = cutoff
    
    query += """
        GROUP BY killer_id, killer_name
        ORDER BY kills DESC
        LIMIT :limit
    """
    
    result = await session.execute(text(query), params)
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
    limit: int = Query(20, le=100)
):
    """
    Leaderboard de longest kills.
    """
    query = text("""
        SELECT 
            killer_id,
            killer_name,
            victim_name,
            weapon_category,
            weapon_class,
            distance,
            timestamp
        FROM sentinel_kills
        WHERE distance > 50
          AND victim_is_npc = FALSE
          AND killer_is_npc = FALSE
          AND weapon_class NOT ILIKE '%Bleeding%'
          AND weapon_class NOT ILIKE '%Injury%'
          AND weapon_class NOT ILIKE '%Environment%'
          AND weapon_class NOT ILIKE '%Trap%'
          AND weapon_class NOT ILIKE '%Melee%'
          AND weapon_class NOT ILIKE '%Unarmed%'
          AND weapon_class NOT ILIKE '%Mine%'
          AND weapon_class NOT ILIKE '%C4%'
          AND weapon_class NOT ILIKE '%Claymore%'
          AND weapon_class NOT ILIKE '%Explosive%'
          AND weapon_class IS NOT NULL 
          AND weapon_class != ''
          AND weapon_class != 'Unknown'
        ORDER BY distance DESC
        LIMIT :limit
    """)
    
    result = await session.execute(query, {"limit": limit})
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
            killer_id,
            killer_name,
            COUNT(*) as kills,
            AVG(distance) as avg_distance
        FROM sentinel_kills
        WHERE weapon_category = :category
          AND victim_is_npc = FALSE
        GROUP BY killer_id, killer_name
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
    limit: int = Query(50, le=200),
    min_kills: int = Query(5)
):
    """
    Rankings consolidados (K/D Real) usando view sentinel_player_ranks.
    """
    query = text("""
        SELECT player_name, kills, deaths, kd_ratio 
        FROM sentinel_player_ranks 
        WHERE kills >= :min_kills 
        ORDER BY kd_ratio DESC, kills DESC 
        LIMIT :limit
    """)
    result = await session.execute(query, {"min_kills": min_kills, "limit": limit})
    rows = result.fetchall()
    
    return [
        {
            "rank": idx + 1,
            "name": row[0],
            "count": row[1], # kills
            "deaths": row[2],
            "kd": float(row[3])
        }
        for idx, row in enumerate(rows)
    ]

@router.get("/analytics/rivalries")
async def get_top_rivalries(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(10, le=50)
):
    """
    Top rivalidades usando view sentinel_rivalries.
    """
    query = text("SELECT * FROM sentinel_rivalries LIMIT :limit")
    result = await session.execute(query, {"limit": limit})
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
    session: AsyncSession = Depends(get_session)
):
    """
    Histórico detalhado entre dois jogadores.
    """
    # Usando ILIKE para case-insensitive search se necessário, mas SQLAlchemy model usa ==.
    # Vamos manter simples primeiro. Se precisar de case-insensitive, ajustar.
    # Assumindo nomes exatos como vêm do frontend (select dropdown).
    
    query = select(SentinelKill).where(
        ((SentinelKill.killer_name == player1) & (SentinelKill.victim_name == player2)) |
        ((SentinelKill.killer_name == player2) & (SentinelKill.victim_name == player1))
    ).order_by(SentinelKill.timestamp.desc())
    
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
