from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.all_models import LogLogin

router = APIRouter()

@router.get("/", response_model=List[LogLogin])
async def get_login_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    steam_id: Optional[str] = None,
    action: Optional[str] = None,  # login / logout
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """
    Busca histórico de logins e logouts.
    """
    query = select(LogLogin).order_by(LogLogin.timestamp.desc())
    
    # Global Wipe Date Filter
    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogLogin.timestamp >= wipe_dt)
        except ValueError:
            pass

    # Specific Filters
    if steam_id:
        query = query.where(LogLogin.steam_id == steam_id)
    
    if action:
        query = query.where(LogLogin.action == action)
        
    if date_from:
        query = query.where(LogLogin.timestamp >= date_from)
        
    if date_to:
        query = query.where(LogLogin.timestamp <= date_to)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
