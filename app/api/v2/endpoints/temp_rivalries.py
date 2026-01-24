
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
