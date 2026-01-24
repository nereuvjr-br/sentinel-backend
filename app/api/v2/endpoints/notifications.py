from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, and_, or_
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_session
from app.models.notification_v2 import SentinelNotificationLog

router = APIRouter()

@router.get("/", tags=["Notifications"])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    notification_type: Optional[str] = None,
    recipient_phone: Optional[str] = None,
    recipient_steam_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Lista todas as notificações enviadas com filtros opcionais.
    
    **Filtros disponíveis:**
    - `notification_type`: Tipo de notificação (raid_alert, etc)
    - `recipient_phone`: Número do destinatário
    - `recipient_steam_id`: Steam ID do destinatário
    - `status`: Status do envio (success, failed, pending)
    - `start_date`: Data inicial (ISO format)
    - `end_date`: Data final (ISO format)
    """
    stmt = select(SentinelNotificationLog)
    
    # Aplicar filtros
    filters = []
    if notification_type:
        filters.append(SentinelNotificationLog.notification_type == notification_type)
    if recipient_phone:
        filters.append(SentinelNotificationLog.recipient_phone == recipient_phone)
    if recipient_steam_id:
        filters.append(SentinelNotificationLog.recipient_steam_id == recipient_steam_id)
    if status:
        filters.append(SentinelNotificationLog.status == status)
    if start_date:
        filters.append(SentinelNotificationLog.sent_at >= start_date)
    if end_date:
        filters.append(SentinelNotificationLog.sent_at <= end_date)
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    # Ordenar por mais recente
    stmt = stmt.order_by(SentinelNotificationLog.sent_at.desc())
    stmt = stmt.offset(skip).limit(limit)
    
    result = await session.execute(stmt)
    notifications = result.scalars().all()
    
    # Contar total
    count_stmt = select(func.count()).select_from(SentinelNotificationLog)
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total = await session.scalar(count_stmt)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": notifications
    }


@router.get("/stats", tags=["Notifications"])
async def get_notification_stats(
    hours: int = Query(24, ge=1, le=168),  # Últimas 24h por padrão, máx 7 dias
    session: AsyncSession = Depends(get_session)
):
    """
    Retorna estatísticas de notificações enviadas.
    
    **Métricas:**
    - Total de notificações enviadas
    - Taxa de sucesso/falha
    - Distribuição por tipo
    - Distribuição por tipo de destinatário
    - Últimas falhas
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Total de notificações
    total_stmt = select(func.count()).select_from(SentinelNotificationLog).where(
        SentinelNotificationLog.sent_at >= cutoff_time
    )
    total = await session.scalar(total_stmt) or 0
    
    # Sucessos
    success_stmt = select(func.count()).select_from(SentinelNotificationLog).where(
        and_(
            SentinelNotificationLog.sent_at >= cutoff_time,
            SentinelNotificationLog.status == "success"
        )
    )
    success_count = await session.scalar(success_stmt) or 0
    
    # Falhas
    failed_stmt = select(func.count()).select_from(SentinelNotificationLog).where(
        and_(
            SentinelNotificationLog.sent_at >= cutoff_time,
            SentinelNotificationLog.status == "failed"
        )
    )
    failed_count = await session.scalar(failed_stmt) or 0
    
    # Por tipo de notificação
    type_stmt = select(
        SentinelNotificationLog.notification_type,
        func.count().label("count")
    ).where(
        SentinelNotificationLog.sent_at >= cutoff_time
    ).group_by(SentinelNotificationLog.notification_type)
    
    type_result = await session.execute(type_stmt)
    by_type = {row[0]: row[1] for row in type_result.all()}
    
    # Por tipo de destinatário
    recipient_type_stmt = select(
        SentinelNotificationLog.recipient_type,
        func.count().label("count")
    ).where(
        SentinelNotificationLog.sent_at >= cutoff_time
    ).group_by(SentinelNotificationLog.recipient_type)
    
    recipient_type_result = await session.execute(recipient_type_stmt)
    by_recipient_type = {row[0]: row[1] for row in recipient_type_result.all()}
    
    # Últimas 10 falhas
    recent_failures_stmt = select(SentinelNotificationLog).where(
        and_(
            SentinelNotificationLog.sent_at >= cutoff_time,
            SentinelNotificationLog.status == "failed"
        )
    ).order_by(SentinelNotificationLog.sent_at.desc()).limit(10)
    
    recent_failures_result = await session.execute(recent_failures_stmt)
    recent_failures = recent_failures_result.scalars().all()
    
    return {
        "period_hours": hours,
        "total_notifications": total,
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": round((success_count / total * 100) if total > 0 else 0, 2),
        "by_notification_type": by_type,
        "by_recipient_type": by_recipient_type,
        "recent_failures": [
            {
                "id": f.id,
                "sent_at": f.sent_at,
                "recipient_phone": f.recipient_phone,
                "recipient_name": f.recipient_name,
                "notification_type": f.notification_type,
                "error_message": f.error_message
            }
            for f in recent_failures
        ]
    }


@router.get("/{notification_id}", tags=["Notifications"])
async def get_notification_detail(
    notification_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Retorna detalhes completos de uma notificação específica.
    """
    notification = await session.get(SentinelNotificationLog, notification_id)
    
    if not notification:
        return {"error": "Notification not found"}, 404
    
    return notification
