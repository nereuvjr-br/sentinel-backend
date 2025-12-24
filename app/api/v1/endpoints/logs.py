import math
from datetime import datetime
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Query
from sqlmodel import select, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.models.all_models import LogChat, LogKill

router = APIRouter()

@router.get("/chat", response_model=List[LogChat])
async def get_chat_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
    offset: int = 0,
    steam_id: Optional[str] = None,
    channel: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Busca histórico de chat com filtros opcionais.
    """
    query = select(LogChat).order_by(LogChat.timestamp.desc())
    
    if settings.WIPE_DATE:
        try:
            # Assumes ISO format: "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SS"
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogChat.timestamp >= wipe_dt)
        except ValueError:
            pass # Ignore invalid date format

    
    if steam_id:
        query = query.where(LogChat.steam_id == steam_id)
    if channel:
        query = query.where(LogChat.channel == channel)
    if search:
        # Busca case-insensitive no Postgres
        query = query.where(LogChat.message.ilike(f"%{search}%"))
        
    query = query.offset(offset).limit(limit)
    # CORREÇÃO: .execute() + .scalars()
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/killfeed", response_model=List[Any])
async def get_killfeed(
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
    killer_id: Optional[str] = None,
    victim_id: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Retorna o feed de mortes (PvP/PvE).
    Calcula a distância do engajamento com base nas coordenadas server-side.
    """
    query = select(LogKill).order_by(LogKill.timestamp.desc())
    
    if settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            query = query.where(LogKill.timestamp >= wipe_dt)
        except ValueError:
            pass

    
    if killer_id:
        query = query.where(LogKill.killer_id == killer_id)
    if victim_id:
        query = query.where(LogKill.victim_id == victim_id)
    if search:
        # Busca por nome do killer ou victim
        query = query.where(
            (LogKill.killer_name.ilike(f"%{search}%")) | 
            (LogKill.victim_name.ilike(f"%{search}%"))
        )
        
    query = query.offset(offset).limit(limit)
    # CORREÇÃO: .execute() + .scalars()
    result = await session.execute(query)
    kills = result.scalars().all()
    
    # Processar distância
    response = []
    for kill in kills:
        dist = None
        if kill.killer_loc and kill.victim_loc:
            try:
                # Coordenadas geralmente são X, Y, Z. SCUM usa CM?
                # Distancia Euclidiana 3D
                x1, y1, z1 = float(kill.killer_loc.get('X', 0)), float(kill.killer_loc.get('Y', 0)), float(kill.killer_loc.get('Z', 0))
                x2, y2, z2 = float(kill.victim_loc.get('X', 0)), float(kill.victim_loc.get('Y', 0)), float(kill.victim_loc.get('Z', 0))
                
                dist_cm = math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
                dist = dist_cm / 100.0 # Converter cm -> metros
            except (ValueError, TypeError):
                dist = None
        
        # Converte para dict e adiciona campo
        k_dict = kill.model_dump()
        k_dict['distance'] = dist
        response.append(k_dict)
        
    return response
