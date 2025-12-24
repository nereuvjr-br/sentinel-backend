from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.all_models import LogAdmin

router = APIRouter()

@router.get("/", response_model=List[LogAdmin])
async def get_admin_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    steam_id: Optional[str] = None,
    command: Optional[str] = None
):
    """
    Busca logs de comandos administrativos.
    """
    query = select(LogAdmin).order_by(LogAdmin.timestamp.desc())
    
    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogAdmin.timestamp >= wipe_dt)
        except ValueError:
            pass
            
    if steam_id:
        query = query.where(LogAdmin.steam_id == steam_id)
        
    if command:
        query = query.where(LogAdmin.command.ilike(f"%{command}%"))

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
