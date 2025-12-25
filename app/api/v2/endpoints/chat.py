from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.chat_v2 import SentinelChatMessage

router = APIRouter()

@router.get("", response_model=List[SentinelChatMessage])
async def get_chat_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    steam_id: Optional[str] = None,
    channel: Optional[str] = None,
    search: Optional[str] = None,
    show_automated: bool = False,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """
    Lista logs de Chat (V2).
    """
    query = select(SentinelChatMessage).order_by(SentinelChatMessage.timestamp.desc())

    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
         try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(SentinelChatMessage.timestamp >= wipe_dt)
         except ValueError:
            pass

    if steam_id:
        query = query.where(SentinelChatMessage.steam_id == steam_id)
        
    if channel:
        query = query.where(SentinelChatMessage.channel == channel)
        
    if search:
        from sqlmodel import or_
        query = query.where(or_(
            SentinelChatMessage.message.contains(search),
            SentinelChatMessage.player_name.contains(search),
            SentinelChatMessage.steam_id.contains(search)
        ))
        
    if not show_automated:
        query = query.where(SentinelChatMessage.is_automated == False)

    if date_from:
        query = query.where(SentinelChatMessage.timestamp >= date_from)
    if date_to:
        query = query.where(SentinelChatMessage.timestamp <= date_to)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
