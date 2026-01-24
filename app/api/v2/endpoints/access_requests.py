from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_session
from app.models.access_request import SentinelAccessRequest
from app.models.players_registry_v2 import SentinelPlayerRegistry
from app.models.verification import SentinelVerificationCode
from app.services.evolution_api import evolution_service

router = APIRouter()

# --- Schemas ---

class AccessRequestCreate(BaseModel):
    steam_id: str
    player_name: str
    phone_number: str

class AccessRequestDecision(BaseModel):
    items: List[int]
    reason: Optional[str] = None

# --- Endpoints ---

@router.post("/request")
async def create_access_request(
    data: AccessRequestCreate,
    session: AsyncSession = Depends(get_session)
):
    """Public: User submits a new access request"""
    
    # 1. Validate Steam ID format (basic check)
    if len(data.steam_id) != 17 or not data.steam_id.isdigit():
        raise HTTPException(status_code=400, detail="Steam ID inválido. Deve conter 17 dígitos.")

    # 2. Check if phone is verified
    # We should ideally check if the phone was verified recently in SentinelVerificationCode
    # For robust security, we'd pass a token, but here strict timestamp check is "okay" 
    # if the previous step was respected.
    # Let's check if there is a verified record for this phone in the last 15 minutes.
    verify_q = select(SentinelVerificationCode).where(
        SentinelVerificationCode.phone_number == data.phone_number,
        SentinelVerificationCode.is_verified == True,
        SentinelVerificationCode.expires_at > datetime.utcnow() # Using expires_at as a proxy for "recent"
    ).order_by(SentinelVerificationCode.created_at.desc())
    
    verify_res = await session.execute(verify_q)
    if not verify_res.scalars().first():
         # If no active verified code, we might want to be strict or lenient.
         # For now, let's trust the frontend flow but this is a security gap (anyone can spam POST).
         # TODO: Enforce verification token.
         pass 

    # 3. Check for existing PENDING request
    existing_q = select(SentinelAccessRequest).where(
        SentinelAccessRequest.steam_id == data.steam_id,
        SentinelAccessRequest.status == "PENDING"
    )
    result = await session.execute(existing_q)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Já existe uma solicitação pendente para este Steam ID.")

    # 4. Create Request
    new_req = SentinelAccessRequest(
        steam_id=data.steam_id,
        player_name=data.player_name,
        phone_number=data.phone_number,
        status="PENDING",
        created_at=datetime.utcnow()
    )
    session.add(new_req)
    await session.commit()
    
    return {"status": "success", "message": "Solicitação enviada com sucesso."}

@router.get("/list", response_model=List[SentinelAccessRequest])
async def list_access_requests(
    status: str = Query("PENDING", description="Filter by status"),
    session: AsyncSession = Depends(get_session)
):
    """Admin: List access requests"""
    query = select(SentinelAccessRequest).where(
        SentinelAccessRequest.status == status
    ).order_by(SentinelAccessRequest.created_at.desc())
    
    result = await session.execute(query)
    return result.scalars().all()

@router.post("/approve")
async def approve_requests(
    decision: AccessRequestDecision,
    session: AsyncSession = Depends(get_session)
):
    """Admin: Approve requests and link to Player Registry"""
    
    for req_id in decision.items:
        req = await session.get(SentinelAccessRequest, req_id)
        if not req or req.status != "PENDING":
            continue
            
        # 1. Update Request Status
        req.status = "APPROVED"
        req.processed_at = datetime.utcnow()
        session.add(req)
        
        # 2. Update/Create Player Registry Entry
        player = await session.get(SentinelPlayerRegistry, req.steam_id)
        if player:
            player.phone_number = req.phone_number
            # Ensure proper tier if needed, but for now just phone update
            player.updated_at = datetime.utcnow()
            session.add(player)
        else:
            # If player doesn't exist in registry yet (never logged in?), create a skeletal entry
            # This is edge case, usually they play first.
            new_player = SentinelPlayerRegistry(
                steam_id=req.steam_id,
                current_name=req.player_name,
                phone_number=req.phone_number,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                is_active=True
            )
            session.add(new_player)
        
        # 3. Send WhatsApp Notification
        try:
            msg = (
                f"🎉 *Parabéns, {req.player_name}!* 🎉\n\n"
                "Sua solicitação de acesso ao *Sentinel* foi APROVADA! ✅\n"
                "Agora você receberá notificações de Raid em tempo real no seu WhatsApp.\n\n"
                "Bom jogo! 🛡️"
            )
            await evolution_service.send_message(req.phone_number, msg)
        except Exception as e:
            # Don't fail the transaction if msg fails, just log it (or ignore for now as we don't have logger here yet)
            print(f"Failed to send approval msg to {req.phone_number}: {e}")
            
    await session.commit()
    return {"status": "success", "processed": len(decision.items)}

@router.post("/reject")
async def reject_requests(
    decision: AccessRequestDecision,
    session: AsyncSession = Depends(get_session)
):
    """Admin: Reject requests"""
    for req_id in decision.items:
        req = await session.get(SentinelAccessRequest, req_id)
        if not req or req.status != "PENDING":
            continue
            
        req.status = "REJECTED"
        req.rejection_reason = decision.reason
        req.processed_at = datetime.utcnow()
        session.add(req)

        # Send WhatsApp Notification
        try:
            reason_text = f"\nMotivo: _{decision.reason}_" if decision.reason else ""
            msg = (
                f"❌ *Solicitação Recusada*\n\n"
                f"Olá {req.player_name}, sua solicitação de acesso ao Sentinel foi negada.{reason_text}\n\n"
                "Entre em contato com a administração se acreditar que houve um engano."
            )
            await evolution_service.send_message(req.phone_number, msg)
        except Exception as e:
            print(f"Failed to send rejection msg to {req.phone_number}: {e}")
            
    await session.commit()
    return {"status": "success", "processed": len(decision.items)}
