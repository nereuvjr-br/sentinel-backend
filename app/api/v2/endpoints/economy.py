from fastapi import APIRouter, Query, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.economy_v2 import SentinelEconomyTrade, SentinelEconomyBalance
from app.core.config import settings
from datetime import datetime

router = APIRouter()

@router.get("/trades/")
async def get_economy_trades(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    search: str = Query(None),
    trade_type: str = Query(None)
):
    """
    Get economy trade logs with optional filtering.
    
    - **limit**: Maximum number of records to return
    - **offset**: Number of records to skip
    - **search**: Search by player name, steam ID, item class, or trader name
    - **trade_type**: Filter by trade type (Purchase/Sell)
    """
    statement = select(SentinelEconomyTrade)
    
    # Apply wipe date filter if configured
    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            statement = statement.where(SentinelEconomyTrade.timestamp >= wipe_dt)
        except ValueError:
            pass
    
    if search:
        statement = statement.where(
            (SentinelEconomyTrade.player_name.ilike(f"%{search}%")) |
            (SentinelEconomyTrade.steam_id.ilike(f"%{search}%")) |
            (SentinelEconomyTrade.item_class.ilike(f"%{search}%")) |
            (SentinelEconomyTrade.trader_name.ilike(f"%{search}%"))
        )
    
    if trade_type:
        statement = statement.where(SentinelEconomyTrade.trade_type == trade_type)
    
    statement = statement.order_by(SentinelEconomyTrade.timestamp.desc())
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()



@router.get("/balances/")
async def get_economy_balances(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    search: str = Query(None)
):
    """
    Get player balance snapshots.
    
    - **limit**: Maximum number of records to return
    - **offset**: Number of records to skip
    - **search**: Search by player name or steam ID
    """
    statement = select(SentinelEconomyBalance)
    
    # Apply wipe date filter if configured
    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            statement = statement.where(SentinelEconomyBalance.timestamp >= wipe_dt)
        except ValueError:
            pass
    
    if search:
        statement = statement.where(
            (SentinelEconomyBalance.player_name.ilike(f"%{search}%")) |
            (SentinelEconomyBalance.steam_id.ilike(f"%{search}%"))
        )
    
    statement = statement.order_by(SentinelEconomyBalance.timestamp.desc())
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()

