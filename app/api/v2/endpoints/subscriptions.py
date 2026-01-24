from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc, or_
from app.core.database import get_session
from app.models.players_registry_v2 import SentinelPlayerRegistry
from app.models.clan_v2 import SentinelClan
from pydantic import BaseModel

router = APIRouter()

class SubscriptionUpdate(BaseModel):
    target_id: str  # SteamID or ScumClanID (as str)
    target_type: str # "player" or "clan"
    plan_tier: str
    phone_number: Optional[str] = None
    notification_settings: Optional[dict] = None

class SubscriptionCreate(BaseModel):
    target_type: str
    name: str

class ValidationRequest(BaseModel):
    contact: str
    type: str # "player" or "clan"

@router.post("/validate")
async def validate_contact(data: ValidationRequest):
    from app.services.evolution_api import evolution_service
    
    if data.type == "player":
        result = await evolution_service.check_number(data.contact)
        if result.get("exists"):
            return {"valid": True, "formatted": result.get("jid").split("@")[0] if result.get("jid") else data.contact}
        else:
             return {"valid": False, "error": result.get("error", "Number not found on WhatsApp")}
             
    elif data.type == "clan":
        result = await evolution_service.check_group(data.contact)
        if result.get("exists"):
            return {"valid": True, "formatted": result.get("jid"), "name": result.get("name")}
        else:
             return {"valid": False, "error": result.get("error", "Group not found or Bot not in group")}
             
    return {"valid": False, "error": "Invalid type"}

@router.post("/create")
async def create_subscription(
    data: SubscriptionCreate,
    session: AsyncSession = Depends(get_session)
):
    from datetime import datetime
    if data.target_type == "player":
        # Check if exists
        existing = await session.get(SentinelPlayerRegistry, data.target_id)
        if existing:
            raise HTTPException(status_code=400, detail="Player already exists")
            
        new_player = SentinelPlayerRegistry(
            steam_id=data.target_id,
            current_name=data.name,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            plan_tier="free"
        )
        session.add(new_player)
        await session.commit()
        return {"status": "created", "id": new_player.steam_id}

    elif data.target_type == "clan":
        # Check if exists
        try:
            clan_id = int(data.target_id)
        except:
             raise HTTPException(status_code=400, detail="Clan ID must be numeric")

        existing = await session.execute(select(SentinelClan).where(SentinelClan.scum_clan_id == clan_id))
        if existing.scalar_one_or_none():
             raise HTTPException(status_code=400, detail="Clan already exists")
             
        new_clan = SentinelClan(
            scum_clan_id=clan_id,
            name=data.name,
            plan_tier="free"
        )
        session.add(new_clan)
        await session.commit()
        return {"status": "created", "id": new_clan.scum_clan_id}
        
    else:
        raise HTTPException(status_code=400, detail="Invalid target type")

@router.get("/players")
async def list_player_subscriptions(
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(SentinelPlayerRegistry)
    if search:
        stmt = stmt.where(or_(
            SentinelPlayerRegistry.current_name.ilike(f"%{search}%"),
            SentinelPlayerRegistry.steam_id.ilike(f"%{search}%")
        ))
    stmt = stmt.limit(50)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.get("/clans")
async def list_clan_subscriptions(
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(SentinelClan)
    if search:
        stmt = stmt.where(SentinelClan.name.ilike(f"%{search}%"))
    stmt = stmt.limit(50)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.post("/update")
async def update_subscription(
    data: SubscriptionUpdate,
    session: AsyncSession = Depends(get_session)
):
    if data.target_type == "player":
        target = await session.get(SentinelPlayerRegistry, data.target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Player not found")
        
        target.plan_tier = data.plan_tier
        if data.phone_number is not None:
             target.phone_number = data.phone_number
        if data.notification_settings:
            target.notification_settings = data.notification_settings
        
        session.add(target)
        await session.commit()
        return {"status": "success", "tier": target.plan_tier}
    
    elif data.target_type == "clan":
        # Clan ID sent as string, convert to int? Or maybe we query by scum_clan_id
        target = await session.execute(select(SentinelClan).where(SentinelClan.scum_clan_id == int(data.target_id)))
        clan = target.scalar_one_or_none()
        
        if not clan:
            raise HTTPException(status_code=404, detail="Clan not found")
            
        clan.plan_tier = data.plan_tier
        if data.phone_number is not None:
             clan.whatsapp_group_id = data.phone_number
        if data.notification_settings:
            clan.notification_settings = data.notification_settings
            
        session.add(clan)
        await session.commit()
        return {"status": "success", "tier": clan.plan_tier}
        
    else:
        raise HTTPException(status_code=400, detail="Invalid target type")
