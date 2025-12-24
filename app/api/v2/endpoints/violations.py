from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.violation_v2 import SentinelViolation

router = APIRouter()

@router.get("/", response_model=List[SentinelViolation])
async def get_violation_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    steam_id: Optional[str] = None,
    violation_class: Optional[str] = None,
    min_suspicious_count: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """
    Lista logs de violações (V2).
    """
    query = select(SentinelViolation).order_by(SentinelViolation.timestamp.desc())

    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
         try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(SentinelViolation.timestamp >= wipe_dt)
         except ValueError:
            pass

    if search:
        from sqlmodel import or_
        query = query.where(or_(
            SentinelViolation.player_name.contains(search),
            SentinelViolation.steam_id.contains(search),
            SentinelViolation.violation_class.contains(search),
            SentinelViolation.description.contains(search)
        ))

    if steam_id:
        query = query.where(SentinelViolation.steam_id == steam_id)
        
    if violation_class:
        query = query.where(SentinelViolation.violation_class == violation_class)
        
    if min_suspicious_count is not None:
        query = query.where(SentinelViolation.suspicious_count >= min_suspicious_count)

    if date_from:
        query = query.where(SentinelViolation.timestamp >= date_from)
    if date_to:
        query = query.where(SentinelViolation.timestamp <= date_to)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
