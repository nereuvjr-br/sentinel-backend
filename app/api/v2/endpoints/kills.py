from datetime import datetime
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.kill_v2 import SentinelKill
from app.models.players_registry_v2 import SentinelPlayerRegistry

router = APIRouter()

@router.get("")
async def get_kill_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    killer_id: Optional[str] = None,
    victim_id: Optional[str] = None,
    weapon: Optional[str] = None,
    is_event: Optional[bool] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Lista histórico de Kills (V2) enriquecido com dados do Registry.
    """
    KillerReg = aliased(SentinelPlayerRegistry)
    VictimReg = aliased(SentinelPlayerRegistry)
    
    query = select(
        SentinelKill, 
        KillerReg.current_name.label("killer_registry_name"),
        KillerReg.squad_name.label("killer_registry_clan"),
        VictimReg.current_name.label("victim_registry_name"),
        VictimReg.squad_name.label("victim_registry_clan")
    ).outerjoin(
        KillerReg, SentinelKill.killer_id == KillerReg.steam_id
    ).outerjoin(
        VictimReg, SentinelKill.victim_id == VictimReg.steam_id
    ).order_by(SentinelKill.timestamp.desc())

    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
         try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(SentinelKill.timestamp >= wipe_dt)
         except ValueError:
            pass

    if search:
        # Search in names, IDs and weapon
        from sqlmodel import or_
        query = query.where(or_(
            SentinelKill.killer_name.contains(search),
            SentinelKill.victim_name.contains(search),
            SentinelKill.killer_id.contains(search),
            SentinelKill.victim_id.contains(search),
            SentinelKill.weapon.contains(search),
            KillerReg.current_name.contains(search),
            KillerReg.squad_name.contains(search),
            VictimReg.current_name.contains(search),
            VictimReg.squad_name.contains(search)
        ))

    if killer_id:
        query = query.where(SentinelKill.killer_id == killer_id)
    if victim_id:
        query = query.where(SentinelKill.victim_id == victim_id)
    if weapon:
        query = query.where(SentinelKill.weapon.contains(weapon))
    if is_event is not None:
        query = query.where(SentinelKill.is_event == is_event)
    else:
        # Default: Hide events
        query = query.where(SentinelKill.is_event == False)

    if date_from:
        query = query.where(SentinelKill.timestamp >= date_from)
    if date_to:
        query = query.where(SentinelKill.timestamp <= date_to)

    query = query.offset(offset).limit(limit)
    
    result = await session.execute(query)
    
    logs = []
    for row in result.all():
        kill_obj = row[0]
        data = kill_obj.model_dump()
        data["killer_registry_name"] = row.killer_registry_name
        data["killer_registry_clan"] = row.killer_registry_clan
        data["victim_registry_name"] = row.victim_registry_name
        data["victim_registry_clan"] = row.victim_registry_clan
        logs.append(data)
        
    return logs
