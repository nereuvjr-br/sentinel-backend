from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.all_models import LogVehicle

router = APIRouter()

@router.get("/", response_model=List[LogVehicle])
async def get_vehicle_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    vehicle_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Busca logs de veículos (Destroyed, Expired, etc).
    """
    query = select(LogVehicle).order_by(LogVehicle.timestamp.desc())
    
    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogVehicle.timestamp >= wipe_dt)
        except ValueError:
            pass
            
    if vehicle_id:
        query = query.where(LogVehicle.vehicle_id == vehicle_id)
        
    if owner_id:
        query = query.where(LogVehicle.owner_id == owner_id)
        
    if search:
        query = query.where(LogVehicle.vehicle_name.ilike(f"%{search}%"))

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
