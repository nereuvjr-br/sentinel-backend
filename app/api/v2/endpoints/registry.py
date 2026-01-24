from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import select, col, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.players_registry_v2 import SentinelPlayerRegistry, SentinelNameChange
from app.models.clan_v2 import SentinelClan, SentinelClanMember

router = APIRouter()

@router.get("/players", response_model=List[SentinelPlayerRegistry])
async def get_players_registry(
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    sort_by: Optional[str] = "last_seen",
    sort_desc: bool = True
):
    """
    Lista registro de players (SCUM.db sync).
    """
    query = select(SentinelPlayerRegistry)
    
    if search:
        query = query.where(or_(
            col(SentinelPlayerRegistry.current_name).ilike(f"%{search}%"),
            col(SentinelPlayerRegistry.steam_id).ilike(f"%{search}%"),
            col(SentinelPlayerRegistry.squad_name).ilike(f"%{search}%")
        ))
        
    # Sorting
    if hasattr(SentinelPlayerRegistry, sort_by):
        field = getattr(SentinelPlayerRegistry, sort_by)
        query = query.order_by(field.desc() if sort_desc else field.asc())
    else:
        query = query.order_by(SentinelPlayerRegistry.last_seen.desc())
        
    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/players/count")
async def get_players_count(
    session: AsyncSession = Depends(get_session),
    search: Optional[str] = None
):
    query = select(func.count(SentinelPlayerRegistry.steam_id))
    if search:
        query = query.where(or_(
            col(SentinelPlayerRegistry.current_name).ilike(f"%{search}%"),
            col(SentinelPlayerRegistry.steam_id).ilike(f"%{search}%"),
            col(SentinelPlayerRegistry.squad_name).ilike(f"%{search}%")
        ))
    result = await session.execute(query)
    return result.scalar_one()

@router.get("/clans", response_model=List[SentinelClan])
async def get_clans_registry(
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None
):
    query = select(SentinelClan)
    
    if search:
        query = query.where(or_(
            col(SentinelClan.name).ilike(f"%{search}%"),
            col(SentinelClan.description).ilike(f"%{search}%")
        ))
        
    query = query.order_by(SentinelClan.member_count.desc())
    query = query.offset(offset).limit(limit)
    
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/clans/count")
async def get_clans_count(
    session: AsyncSession = Depends(get_session),
    search: Optional[str] = None
):
    query = select(func.count(SentinelClan.id))
    if search:
        query = query.where(or_(
            col(SentinelClan.name).ilike(f"%{search}%"),
            col(SentinelClan.description).ilike(f"%{search}%")
        ))
    result = await session.execute(query)
    return result.scalar_one()

@router.get("/summary")
async def get_registry_summary(session: AsyncSession = Depends(get_session)):
    """Retorna estatísticas rápidas do registro"""
    
    players_count = await session.execute(select(func.count(SentinelPlayerRegistry.steam_id)))
    clans_count = await session.execute(select(func.count(SentinelClan.id)))
    
    # Active players (last 24h)
    from datetime import datetime, timedelta
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    active_players = await session.execute(select(func.count(SentinelPlayerRegistry.steam_id)).where(SentinelPlayerRegistry.last_seen >= one_day_ago))

    return {
        "total_players": players_count.scalar_one(),
        "total_clans": clans_count.scalar_one(),
        "active_players_24h": active_players.scalar_one()
    }

# Updates
from pydantic import BaseModel
from fastapi import HTTPException

class PlayerUpdate(BaseModel):
    notes: Optional[str] = None
    phone_number: Optional[str] = None

class ClanUpdate(BaseModel):
    whatsapp_group_id: Optional[str] = None

@router.patch("/players/{steam_id}", response_model=SentinelPlayerRegistry)
async def update_player(
    steam_id: str,
    update_data: PlayerUpdate,
    session: AsyncSession = Depends(get_session)
):
    player = await session.get(SentinelPlayerRegistry, steam_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if update_data.notes is not None:
        player.notes = update_data.notes
    if update_data.phone_number is not None:
        player.phone_number = update_data.phone_number
        
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player

@router.patch("/clans/{clan_id}", response_model=SentinelClan)
async def update_clan(
    clan_id: int,
    update_data: ClanUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update Clan by internal ID (PK)"""
    clan = await session.get(SentinelClan, clan_id)
    if not clan:
        raise HTTPException(status_code=404, detail="Clan not found")

    if update_data.whatsapp_group_id is not None:
        clan.whatsapp_group_id = update_data.whatsapp_group_id
        
    session.add(clan)
    await session.commit()
    await session.refresh(clan)
    return clan
