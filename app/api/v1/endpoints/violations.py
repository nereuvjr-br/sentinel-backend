from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.all_models import LogViolation

router = APIRouter()

@router.get("/", response_model=List[LogViolation])
async def get_violation_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    steam_id: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Busca logs de violações (gameplay violations).
    """
    query = select(LogViolation).order_by(LogViolation.timestamp.desc())
    
    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogViolation.timestamp >= wipe_dt)
        except ValueError:
            pass
            
    if steam_id:
        query = query.where(LogViolation.steam_id == steam_id)
        
    if type:
        query = query.where(LogViolation.violation_type == type)
        
    if search:
        query = query.where(LogViolation.details.ilike(f"%{search}%"))

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
