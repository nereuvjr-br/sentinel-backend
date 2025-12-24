from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.all_models import LogGameplay

router = APIRouter()

@router.get("/", response_model=List[LogGameplay])
async def get_gameplay_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Busca logs de gameplay (BunkerLock, etc).
    """
    query = select(LogGameplay).order_by(LogGameplay.timestamp.desc())
    
    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogGameplay.timestamp >= wipe_dt)
        except ValueError:
            pass
            
    if event_type:
        query = query.where(LogGameplay.event_type == event_type)
        
    if search:
        query = query.where(LogGameplay.event_name.ilike(f"%{search}%"))

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
