from fastapi import APIRouter, Query, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.economy_v2 import (
    SentinelBankTransaction,
    SentinelMechanicService,
    SentinelBankCard,
    SentinelUnparsedLog,
    SentinelEconomyTrade
)
from app.core.config import settings
from datetime import datetime

router = APIRouter()

# ============================================================================
# BANK TRANSACTIONS
# ============================================================================

@router.get("/bank-transactions/")
async def get_bank_transactions(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    search: str = Query(None),
    transaction_type: str = Query(None)
):
    """
    Get bank transactions (deposits, withdrawals, transfers).
    
    - **limit**: Maximum number of records to return
    - **offset**: Number of records to skip
    - **search**: Search by player name, steam ID, or account number
    - **transaction_type**: Filter by type (deposit/withdraw/transfer)
    """
    statement = select(SentinelBankTransaction)
    
    # Apply wipe date filter if configured
    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            statement = statement.where(SentinelBankTransaction.timestamp >= wipe_dt)
        except ValueError:
            pass
    
    if search:
        statement = statement.where(
            (SentinelBankTransaction.player_name.ilike(f"%{search}%")) |
            (SentinelBankTransaction.steam_id.ilike(f"%{search}%")) |
            (SentinelBankTransaction.account_number.ilike(f"%{search}%"))
        )
    
    if transaction_type:
        statement = statement.where(SentinelBankTransaction.transaction_type == transaction_type)
    
    statement = statement.order_by(SentinelBankTransaction.timestamp.desc())
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()


# ============================================================================
# MECHANIC SERVICES
# ============================================================================

@router.get("/mechanic-services/")
async def get_mechanic_services(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    search: str = Query(None),
    service_type: str = Query(None)
):
    """
    Get mechanic services (Buy, Install, Repair, Remove).
    
    - **limit**: Maximum number of records to return
    - **offset**: Number of records to skip
    - **search**: Search by player name, steam ID, item, or trader
    - **service_type**: Filter by service type (Buy/Install/Repair/Remove)
    """
    statement = select(SentinelMechanicService)
    
    # Apply wipe date filter if configured
    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            statement = statement.where(SentinelMechanicService.timestamp >= wipe_dt)
        except ValueError:
            pass
    
    if search:
        statement = statement.where(
            (SentinelMechanicService.player_name.ilike(f"%{search}%")) |
            (SentinelMechanicService.steam_id.ilike(f"%{search}%")) |
            (SentinelMechanicService.item_class.ilike(f"%{search}%")) |
            (SentinelMechanicService.trader_name.ilike(f"%{search}%"))
        )
    
    if service_type:
        statement = statement.where(SentinelMechanicService.service_type == service_type)
    
    statement = statement.order_by(SentinelMechanicService.timestamp.desc())
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()


# ============================================================================
# BANK CARDS
# ============================================================================

@router.get("/bank-cards/")
async def get_bank_cards(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    search: str = Query(None),
    action: str = Query(None),
    card_type: str = Query(None)
):
    """
    Get bank card management events (purchases and destructions).
    
    - **limit**: Maximum number of records to return
    - **offset**: Number of records to skip
    - **search**: Search by player name, steam ID, or account number
    - **action**: Filter by action (purchased/manually destroyed)
    - **card_type**: Filter by card type (Starter card/Gold card/Classic card)
    """
    statement = select(SentinelBankCard)
    
    # Apply wipe date filter if configured
    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            statement = statement.where(SentinelBankCard.timestamp >= wipe_dt)
        except ValueError:
            pass
    
    if search:
        statement = statement.where(
            (SentinelBankCard.player_name.ilike(f"%{search}%")) |
            (SentinelBankCard.steam_id.ilike(f"%{search}%")) |
            (SentinelBankCard.account_number.ilike(f"%{search}%"))
        )
    
    if action:
        statement = statement.where(SentinelBankCard.action == action)
    
    if card_type:
        statement = statement.where(SentinelBankCard.card_type == card_type)
    
    statement = statement.order_by(SentinelBankCard.timestamp.desc())
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()


# ============================================================================
# UNPARSED LOGS (Debug/Monitoring)
# ============================================================================

@router.get("/unparsed-logs/")
async def get_unparsed_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    log_type: str = Query(None)
):
    """
    Get unparsed logs for debugging and monitoring.
    These are logs that couldn't be recognized by any parser.
    
    - **limit**: Maximum number of records to return
    - **offset**: Number of records to skip
    - **log_type**: Filter by log type (economy, kill, etc.)
    """
    statement = select(SentinelUnparsedLog)
    
    if log_type:
        statement = statement.where(SentinelUnparsedLog.log_type == log_type)
    
    statement = statement.order_by(SentinelUnparsedLog.timestamp.desc())
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()


# ============================================================================
# STATISTICS
# ============================================================================

@router.get("/stats/")
async def get_economy_stats(
    session: AsyncSession = Depends(get_session)
):
    """
    Get economy statistics overview.
    """
    from sqlalchemy import func
    
    # Apply wipe date filter
    wipe_filter = None
    if hasattr(settings, "WIPE_DATE") and settings.WIPE_DATE:
        try:
            wipe_dt = datetime.fromisoformat(settings.WIPE_DATE)
            wipe_filter = wipe_dt
        except ValueError:
            pass
    
    stats = {}
    
    # Bank Transactions
    stmt = select(func.count(SentinelBankTransaction.id))
    if wipe_filter:
        stmt = stmt.where(SentinelBankTransaction.timestamp >= wipe_filter)
    result = await session.execute(stmt)
    stats["total_bank_transactions"] = result.scalar()
    
    # Trades (Compras/Vendas) - NEW
    stmt = select(func.count(SentinelEconomyTrade.id))
    if wipe_filter:
        stmt = stmt.where(SentinelEconomyTrade.timestamp >= wipe_filter)
    result = await session.execute(stmt)
    stats["total_trades"] = result.scalar()
    
    # Mechanic Services
    stmt = select(func.count(SentinelMechanicService.id))
    if wipe_filter:
        stmt = stmt.where(SentinelMechanicService.timestamp >= wipe_filter)
    result = await session.execute(stmt)
    stats["total_mechanic_services"] = result.scalar()
    
    # Bank Cards
    stmt = select(func.count(SentinelBankCard.id))
    if wipe_filter:
        stmt = stmt.where(SentinelBankCard.timestamp >= wipe_filter)
    result = await session.execute(stmt)
    stats["total_bank_card_events"] = result.scalar()
    
    # Unparsed Logs (no wipe filter - always show all)
    stmt = select(func.count(SentinelUnparsedLog.id))
    result = await session.execute(stmt)
    stats["total_unparsed_logs"] = result.scalar()
    
    return stats
