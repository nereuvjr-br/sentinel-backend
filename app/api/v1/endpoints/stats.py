from datetime import datetime
from typing import List, Any
from fastapi import APIRouter, Depends
from sqlalchemy import func, desc
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.all_models import LogKill, LogEconomy

router = APIRouter()

from app.models.kill_v2 import SentinelKill

@router.get("/leaderboard/kills")
async def get_top_killers(
    session: AsyncSession = Depends(get_session),
    limit: int = 10
):
    """
    Retorna o TOP 10 Matadores (V2 Data Source).
    Agrega contagem de rows na tabela SentinelKill agrupado por killer_id.
    """
    # Query: Select killer_id, killer_name, count(*) 
    # Note: killer_name can change, usually we group by ID and pick arbitrary name or latest name.
    # Grouping by Name+ID is safer for display.
    query = (
        select(
            SentinelKill.killer_id, 
            SentinelKill.killer_name, 
            func.count(SentinelKill.id).label("kill_count")
        )
        .where(SentinelKill.killer_id.isnot(None))
        .where(SentinelKill.is_event == False) # Exclude events? Usually yes.
    )

    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(SentinelKill.timestamp >= wipe_dt)
        except ValueError:
            pass

    query = (
        query
        .group_by(SentinelKill.killer_id, SentinelKill.killer_name)
        .order_by(desc("kill_count"))
        .limit(limit)
    )
    
    result = await session.execute(query)
    # Return formatted for Frontend KillStat interface
    return [
        {
            "killer_id": row.killer_id, 
            "killer_name": row.killer_name, 
            "kill_count": row.kill_count
        } 
        for row in result.all()
    ]

@router.get("/economy/top-rich")
async def get_richest_players(
    session: AsyncSession = Depends(get_session),
    limit: int = 10
):
    """
    Placeholder: Como SCUM não loga o 'saldo total', apenas transações, 
    não dá para saber quem é o mais rico só pelos logs de transação sem replay completo.
    
    Retorna as maiores transações recentes.
    """
    query = select(LogEconomy).order_by(LogEconomy.timestamp.desc())

    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogEconomy.timestamp >= wipe_dt)
        except ValueError:
            pass
            
    query = query.limit(limit)
    # CORREÇÃO: .execute() + .scalars()
    result = await session.execute(query)
    return result.scalars().all()
