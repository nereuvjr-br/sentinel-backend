from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.all_models import LogEconomy

router = APIRouter()

@router.get("/", response_model=List[LogEconomy])
async def get_economy_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    steam_id: Optional[str] = None,
    type: Optional[str] = None,
    account_number: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Busca logs de economia (transações, banco, trade).
    """
    query = select(LogEconomy).order_by(LogEconomy.timestamp.desc())
    
    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogEconomy.timestamp >= wipe_dt)
        except ValueError:
            pass
            
    if steam_id:
        query = query.where(LogEconomy.steam_id == steam_id)
        
    if type:
        query = query.where(LogEconomy.type == type)

    if account_number:
         query = query.where(LogEconomy.account_number == account_number)
        
    if search:
        query = query.where(LogEconomy.details.ilike(f"%{search}%"))

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
