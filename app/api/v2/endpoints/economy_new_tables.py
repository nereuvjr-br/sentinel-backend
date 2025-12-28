"""
Economy Analytics API - New Tables
Endpoints para as novas tabelas de análise econômica
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlmodel import select, func
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.economy_analytics_v2 import (
    SentinelPlayerWallet,
    SentinelItemEconomy,
    SentinelEconomyAlert,
    SentinelTraderInventory,
    SentinelAccountRegistry
)
from app.models.admin_economy_v2 import SentinelAdminEconomyAction
from datetime import datetime, timedelta
from typing import List, Optional

router = APIRouter()

# ============================================================================
# PLAYER WALLETS
# ============================================================================

@router.get("/wallets/")
async def get_player_wallets(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    min_net_worth: Optional[float] = None
):
    """
    Lista carteiras de jogadores.
    """
    statement = select(SentinelPlayerWallet)
    
    if search:
        statement = statement.where(
            (SentinelPlayerWallet.player_name.ilike(f"%{search}%")) |
            (SentinelPlayerWallet.steam_id.ilike(f"%{search}%"))
        )
    
    if min_net_worth:
        statement = statement.where(
            (SentinelPlayerWallet.cash + SentinelPlayerWallet.bank + SentinelPlayerWallet.gold) >= min_net_worth
        )
    
    statement = statement.order_by(
        (SentinelPlayerWallet.cash + SentinelPlayerWallet.bank + SentinelPlayerWallet.gold).desc()
    )
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/wallets/top")
async def get_top_wallets(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(20, le=100)
):
    """
    Top jogadores mais ricos (por net worth total).
    """
    query = text("""
        SELECT 
            steam_id,
            player_name,
            cash,
            bank,
            gold,
            (cash + bank + gold) as net_worth,
            total_earned,
            total_spent,
            squad_name,
            last_transaction
        FROM sentinel_player_wallets
        ORDER BY (cash + bank + gold) DESC
        LIMIT :limit
    """)
    
    result = await session.execute(query, {"limit": limit})
    rows = result.fetchall()
    
    return [
        {
            "steam_id": row[0],
            "player_name": row[1],
            "cash": float(row[2]) if row[2] else 0,
            "bank": float(row[3]) if row[3] else 0,
            "gold": float(row[4]) if row[4] else 0,
            "net_worth": float(row[5]) if row[5] else 0,
            "total_earned": float(row[6]) if row[6] else 0,
            "total_spent": float(row[7]) if row[7] else 0,
            "squad_name": row[8],
            "last_transaction": row[9].isoformat() if row[9] else None
        }
        for row in rows
    ]


@router.get("/wallets/{steam_id}")
async def get_player_wallet(
    steam_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Detalhes da carteira de um jogador específico.
    """
    statement = select(SentinelPlayerWallet).where(SentinelPlayerWallet.steam_id == steam_id)
    result = await session.execute(statement)
    wallet = result.scalar_one_or_none()
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    
    return wallet


# ============================================================================
# ITEM ECONOMY
# ============================================================================

@router.get("/items/")
async def get_item_economy(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    demand_level: Optional[str] = None
):
    """
    Lista análise econômica de itens.
    """
    statement = select(SentinelItemEconomy)
    
    if search:
        statement = statement.where(SentinelItemEconomy.item_class.ilike(f"%{search}%"))
    
    if demand_level:
        statement = statement.where(SentinelItemEconomy.demand_level == demand_level)
    
    statement = statement.order_by(SentinelItemEconomy.total_sales.desc())
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/items/trending")
async def get_trending_items(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(20, le=100),
    hours: int = Query(24)
):
    """
    Itens em alta (mais vendidos/comprados recentemente).
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    statement = select(SentinelItemEconomy).where(
        SentinelItemEconomy.period_start >= cutoff
    ).order_by(
        SentinelItemEconomy.total_sales.desc()
    ).limit(limit)
    
    result = await session.execute(statement)
    return result.scalars().all()


# ============================================================================
# ECONOMY ALERTS
# ============================================================================

@router.get("/alerts/")
async def get_economy_alerts(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    alert_type: Optional[str] = None
):
    """
    Lista alertas econômicos.
    """
    statement = select(SentinelEconomyAlert)
    
    if severity:
        statement = statement.where(SentinelEconomyAlert.severity == severity)
    
    if status:
        statement = statement.where(SentinelEconomyAlert.status == status)
    
    if alert_type:
        statement = statement.where(SentinelEconomyAlert.alert_type == alert_type)
    
    statement = statement.order_by(SentinelEconomyAlert.detected_at.desc())
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/alerts/active")
async def get_active_alerts(
    session: AsyncSession = Depends(get_session),
    severity: Optional[str] = None
):
    """
    Alertas ativos (não resolvidos).
    """
    statement = select(SentinelEconomyAlert).where(
        SentinelEconomyAlert.status == 'open'
    )
    
    if severity:
        statement = statement.where(SentinelEconomyAlert.severity == severity)
    
    statement = statement.order_by(SentinelEconomyAlert.detected_at.desc())
    
    result = await session.execute(statement)
    return result.scalars().all()


# ============================================================================
# TRADER INVENTORY
# ============================================================================

@router.get("/traders/")
async def get_trader_inventory(
    session: AsyncSession = Depends(get_session),
    trader_name: Optional[str] = None,
    low_funds: bool = False
):
    """
    Lista inventário de traders.
    """
    statement = select(SentinelTraderInventory)
    
    if trader_name:
        statement = statement.where(SentinelTraderInventory.trader_name == trader_name)
    
    if low_funds:
        statement = statement.where(SentinelTraderInventory.funds < 10000)
    
    statement = statement.order_by(SentinelTraderInventory.snapshot_time.desc())
    
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/traders/{trader_name}")
async def get_trader_details(
    trader_name: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Detalhes de um trader específico (último snapshot).
    """
    statement = select(SentinelTraderInventory).where(
        SentinelTraderInventory.trader_name == trader_name
    ).order_by(SentinelTraderInventory.snapshot_time.desc()).limit(1)
    
    result = await session.execute(statement)
    trader = result.scalar_one_or_none()
    
    if not trader:
        raise HTTPException(status_code=404, detail="Trader não encontrado")
    
    return trader


# ============================================================================
# ACCOUNT REGISTRY
# ============================================================================

@router.get("/accounts/")
async def get_accounts(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    owner_steam_id: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """
    Lista contas bancárias.
    """
    statement = select(SentinelAccountRegistry)
    
    if owner_steam_id:
        statement = statement.where(SentinelAccountRegistry.current_owner_steam_id == owner_steam_id)
    
    if is_active is not None:
        statement = statement.where(SentinelAccountRegistry.is_active == is_active)
    
    statement = statement.order_by(SentinelAccountRegistry.last_transaction.desc())
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/accounts/{account_number}")
async def get_account_details(
    account_number: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Detalhes de uma conta bancária específica.
    """
    statement = select(SentinelAccountRegistry).where(
        SentinelAccountRegistry.account_number == account_number
    )
    
    result = await session.execute(statement)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    return account


# ============================================================================
# ADMIN ECONOMY ACTIONS
# ============================================================================

@router.get("/admin-actions/")
async def get_admin_economy_actions(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    admin_steam_id: Optional[str] = None,
    action_type: Optional[str] = None,
    impact_level: Optional[str] = None,
    is_cash_spawn: Optional[bool] = None
):
    """
    Lista ações econômicas de admins.
    """
    statement = select(SentinelAdminEconomyAction)
    
    if admin_steam_id:
        statement = statement.where(SentinelAdminEconomyAction.admin_steam_id == admin_steam_id)
    
    if action_type:
        statement = statement.where(SentinelAdminEconomyAction.action_type == action_type)
    
    if impact_level:
        statement = statement.where(SentinelAdminEconomyAction.impact_level == impact_level)
    
    if is_cash_spawn is not None:
        statement = statement.where(SentinelAdminEconomyAction.is_cash_spawn == is_cash_spawn)
    
    statement = statement.order_by(SentinelAdminEconomyAction.timestamp.desc())
    statement = statement.limit(limit).offset(offset)
    
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/admin-actions/summary")
async def get_admin_actions_summary(
    session: AsyncSession = Depends(get_session),
    hours: int = Query(24)
):
    """
    Resumo de ações de admin (últimas X horas).
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    query = text("""
        SELECT 
            admin_name,
            COUNT(*) as total_actions,
            COUNT(*) FILTER (WHERE is_cash_spawn = TRUE) as cash_spawns,
            SUM(stack_count) FILTER (WHERE is_cash_spawn = TRUE) as total_cash_spawned,
            COUNT(*) FILTER (WHERE is_weapon_spawn = TRUE) as weapon_spawns,
            COUNT(*) FILTER (WHERE impact_level = 'critical') as critical_actions
        FROM sentinel_admin_economy_actions
        WHERE timestamp >= :cutoff
        GROUP BY admin_name
        ORDER BY total_actions DESC
    """)
    
    result = await session.execute(query, {"cutoff": cutoff})
    rows = result.fetchall()
    
    return [
        {
            "admin_name": row[0],
            "total_actions": row[1],
            "cash_spawns": row[2],
            "total_cash_spawned": float(row[3]) if row[3] else 0,
            "weapon_spawns": row[4],
            "critical_actions": row[5]
        }
        for row in rows
    ]
