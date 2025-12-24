from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.kill_v2 import SentinelKill

router = APIRouter()

@router.get("/", response_model=List[SentinelKill])
async def get_kill_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    killer_id: Optional[str] = None,
    victim_id: Optional[str] = None,
    weapon: Optional[str] = None,
    is_event: Optional[bool] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """
    Lista histórico de Kills (V2).
    """
    query = select(SentinelKill).order_by(SentinelKill.timestamp.desc())

    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
         try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(SentinelKill.timestamp >= wipe_dt)
         except ValueError:
            pass

    if search:
        # Search in names, IDs and weapon
        from sqlmodel import or_
        query = query.where(or_(
            SentinelKill.killer_name.contains(search),
            SentinelKill.victim_name.contains(search),
            SentinelKill.killer_id.contains(search),
            SentinelKill.victim_id.contains(search),
            SentinelKill.weapon.contains(search)
        ))

    if killer_id:
        query = query.where(SentinelKill.killer_id == killer_id)
    if victim_id:
        query = query.where(SentinelKill.victim_id == victim_id)
    if weapon:
        query = query.where(SentinelKill.weapon.contains(weapon))
    if is_event is not None:
        query = query.where(SentinelKill.is_event == is_event)

    if date_from:
        query = query.where(SentinelKill.timestamp >= date_from)
    if date_to:
        query = query.where(SentinelKill.timestamp <= date_to)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
