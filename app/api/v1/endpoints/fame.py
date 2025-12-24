from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.all_models import LogFame

router = APIRouter()

@router.get("/", response_model=List[LogFame])
async def get_fame_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    steam_id: Optional[str] = None,
    # reason: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Busca logs de pontos de fama.
    """
    query = select(LogFame).order_by(LogFame.timestamp.desc())
    
    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogFame.timestamp >= wipe_dt)
        except ValueError:
            pass
            
    if steam_id:
        query = query.where(LogFame.steam_id == steam_id)
        
    if search:
        query = query.where(LogFame.reason.ilike(f"%{search}%"))

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
