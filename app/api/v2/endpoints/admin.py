from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.admin_v2 import SentinelAdminCommand

router = APIRouter()

@router.get("", response_model=List[SentinelAdminCommand])
async def get_admin_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    admin_id: Optional[str] = None,
    command_type: Optional[str] = None,
    target_id: Optional[str] = None,
    show_automated: bool = False,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """
    Lista logs de comandos de Admin (V2).
    """
    query = select(SentinelAdminCommand).order_by(SentinelAdminCommand.timestamp.desc())

    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
         try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(SentinelAdminCommand.timestamp >= wipe_dt)
         except ValueError:
            pass
    
    if search:
        from sqlmodel import or_
        query = query.where(or_(
            SentinelAdminCommand.raw_command.contains(search),
            SentinelAdminCommand.admin_name.contains(search),
            SentinelAdminCommand.target_name.contains(search),
            SentinelAdminCommand.admin_steam_id.contains(search)
        ))

    if admin_id:
        query = query.where(SentinelAdminCommand.admin_steam_id == admin_id)
    
    if command_type:
        query = query.where(SentinelAdminCommand.command_type == command_type)
        
    if target_id:
        query = query.where(SentinelAdminCommand.target_steam_id == target_id)
        
    if not show_automated:
        query = query.where(SentinelAdminCommand.is_automated == False)

    if date_from:
        query = query.where(SentinelAdminCommand.timestamp >= date_from)
    if date_to:
        query = query.where(SentinelAdminCommand.timestamp <= date_to)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
