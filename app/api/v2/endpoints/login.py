from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.login_v2 import SentinelLogin

router = APIRouter()

@router.get("/", response_model=List[SentinelLogin])
async def get_login_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    action: Optional[str] = None,  # Login / Logout
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """
    Lista histórico de logins (V2).
    """
    query = select(SentinelLogin).order_by(SentinelLogin.timestamp.desc())
    
    # Global Wipe Date Filter
    if settings.get("WIPE_DATE"): # Use .get() if WIPE_DATE might not be in settings object proper
        try:
             pass
        except:
             pass
             
    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
         try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(SentinelLogin.timestamp >= wipe_dt)
         except ValueError:
            pass

    if search:
        from sqlmodel import or_
        query = query.where(or_(
            SentinelLogin.player_name.contains(search),
            SentinelLogin.steam_id.contains(search),
            SentinelLogin.ip_address.contains(search)
        ))

    if steam_id:
        query = query.where(SentinelLogin.steam_id == steam_id)
    
    if action:
        query = query.where(SentinelLogin.action == action)
        
    if date_from:
        query = query.where(SentinelLogin.timestamp >= date_from)
        
    if date_to:
        query = query.where(SentinelLogin.timestamp <= date_to)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
