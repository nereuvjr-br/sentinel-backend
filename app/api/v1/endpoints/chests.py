from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.all_models import LogChest

router = APIRouter()

@router.get("/", response_model=List[LogChest])
async def get_chest_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    entity_id: Optional[str] = None,
    owner_id: Optional[str] = None
):
    """
    Busca logs de baús (ownership changed/claimed).
    """
    query = select(LogChest).order_by(LogChest.timestamp.desc())
    
    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogChest.timestamp >= wipe_dt)
        except ValueError:
            pass
            
    if entity_id:
        query = query.where(LogChest.entity_id == entity_id)
        
    if owner_id:
        # Busca tanto no old quanto no new owner
        query = query.where(
            or_(
                LogChest.old_owner_id == owner_id,
                LogChest.new_owner_id == owner_id
            )
        )

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
