from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_session
from app.services.monitoring_service import monitoring_service
from app.models.monitoring_v2 import (
    SentinelParserMetrics,
    SentinelDatabaseHealth,
    SentinelIngestionLog,
    SentinelSystemAlert
)

router = APIRouter()


@router.get("/health")
async def get_system_health(db: AsyncSession = Depends(get_session)):
    """
    Retorna um relatório completo de saúde do sistema.
    Inclui status de parsers, banco de dados, alertas e ingestões recentes.
    """
    try:
        report = await monitoring_service.get_system_health_report(db)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")


@router.get("/parsers")
async def get_parser_metrics(db: AsyncSession = Depends(get_session)):
    """
    Retorna métricas detalhadas de todos os parsers.
    """
    stmt = select(SentinelParserMetrics).order_by(SentinelParserMetrics.parser_name)
    result = await db.execute(stmt)
    metrics = result.scalars().all()
    
    return {
        "parsers": [
            {
                "name": m.parser_name,
                "is_healthy": m.is_healthy,
                "success_rate": m.success_rate,
                "total_processed": m.total_lines_processed,
                "total_success": m.total_lines_success,
                "total_failed": m.total_lines_failed,
                "total_unparsed": m.total_unparsed,
                "avg_parse_time_ms": m.avg_parse_time_ms,
                "last_batch_size": m.last_batch_size,
                "last_batch_time_ms": m.last_batch_time_ms,
                "error_count_last_hour": m.error_count_last_hour,
                "last_error": m.last_error,
                "last_processed_at": m.last_processed_at.isoformat() if m.last_processed_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None
            }
            for m in metrics
        ]
    }


@router.get("/database/snapshots")
async def get_database_snapshots(
    limit: int = Query(default=10, le=100),
    db: AsyncSession = Depends(get_session)
):
    """
    Retorna os últimos snapshots de saúde do banco de dados.
    """
    stmt = select(SentinelDatabaseHealth).order_by(
        desc(SentinelDatabaseHealth.snapshot_at)
    ).limit(limit)
    
    result = await db.execute(stmt)
    snapshots = result.scalars().all()
    
    return {
        "snapshots": [
            {
                "snapshot_at": s.snapshot_at.isoformat(),
                "is_healthy": s.is_healthy,
                "health_issues": s.health_issues,
                "counts": {
                    "admin_commands": s.count_admin_commands,
                    "chat_messages": s.count_chat_messages,
                    "logins": s.count_logins,
                    "kills": s.count_kills,
                    "economy_trades": s.count_economy_trades,
                    "economy_balances": s.count_economy_balances,
                    "bank_transactions": s.count_bank_transactions,
                    "mechanic_services": s.count_mechanic_services,
                    "bank_cards": s.count_bank_cards,
                    "raids": s.count_raids,
                    "crafting": s.count_crafting,
                    "chest_events": s.count_chest_events,
                    "fame_events": s.count_fame_events,
                    "violations": s.count_violations,
                    "vehicles": s.count_vehicles,
                    "unparsed_logs": s.count_unparsed_logs,
                    "processed_files": s.count_processed_files,
                    "player_wallets": s.count_player_wallets,
                    "item_economy": s.count_item_economy,
                    "economy_alerts": s.count_economy_alerts,
                    "trader_inventory": s.count_trader_inventory,
                    "account_registry": s.count_account_registry
                },
                "growth_rates": {
                    "kills_per_min": s.growth_rate_kills,
                    "trades_per_min": s.growth_rate_trades,
                    "logins_per_min": s.growth_rate_logins
                }
            }
            for s in snapshots
        ]
    }


@router.get("/ingestion/logs")
async def get_ingestion_logs(
    limit: int = Query(default=50, le=200),
    log_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Retorna logs de ingestão recentes com filtros opcionais.
    """
    stmt = select(SentinelIngestionLog)
    
    filters = []
    if log_type:
        filters.append(SentinelIngestionLog.log_type == log_type)
    if status:
        filters.append(SentinelIngestionLog.status == status)
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    stmt = stmt.order_by(desc(SentinelIngestionLog.started_at)).limit(limit)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "filename": log.filename,
                "log_type": log.log_type,
                "bytes_processed": log.bytes_processed,
                "lines_processed": log.lines_processed,
                "lines_success": log.lines_success,
                "lines_failed": log.lines_failed,
                "processing_time_ms": log.processing_time_ms,
                "throughput_lines_per_sec": log.throughput_lines_per_sec,
                "status": log.status,
                "error_message": log.error_message,
                "offset_start": log.offset_start,
                "offset_end": log.offset_end,
                "started_at": log.started_at.isoformat(),
                "completed_at": log.completed_at.isoformat() if log.completed_at else None
            }
            for log in logs
        ]
    }


@router.get("/alerts")
async def get_system_alerts(
    status: Optional[str] = Query(default="open"),
    severity: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_session)
):
    """
    Retorna alertas do sistema com filtros opcionais.
    """
    stmt = select(SentinelSystemAlert)
    
    filters = []
    if status:
        filters.append(SentinelSystemAlert.status == status)
    if severity:
        filters.append(SentinelSystemAlert.severity == severity)
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    stmt = stmt.order_by(desc(SentinelSystemAlert.detected_at)).limit(limit)
    
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    return {
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "component": a.component,
                "title": a.title,
                "description": a.description,
                "evidence": a.evidence,
                "status": a.status,
                "acknowledged_by": a.acknowledged_by,
                "resolved_by": a.resolved_by,
                "resolution_notes": a.resolution_notes,
                "detected_at": a.detected_at.isoformat(),
                "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None
            }
            for a in alerts
        ]
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    acknowledged_by: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Marca um alerta como reconhecido.
    """
    stmt = select(SentinelSystemAlert).where(SentinelSystemAlert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    alert.status = "acknowledged"
    alert.acknowledged_by = acknowledged_by
    alert.acknowledged_at = datetime.utcnow()
    
    db.add(alert)
    await db.commit()
    
    return {"message": "Alerta reconhecido com sucesso", "alert_id": alert_id}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    resolved_by: str,
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Marca um alerta como resolvido.
    """
    stmt = select(SentinelSystemAlert).where(SentinelSystemAlert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    alert.status = "resolved"
    alert.resolved_by = resolved_by
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = resolution_notes
    
    db.add(alert)
    await db.commit()
    
    return {"message": "Alerta resolvido com sucesso", "alert_id": alert_id}


@router.get("/stats/summary")
async def get_monitoring_summary(db: AsyncSession = Depends(get_session)):
    """
    Retorna um resumo executivo do monitoramento.
    """
    # Última snapshot
    stmt = select(SentinelDatabaseHealth).order_by(
        desc(SentinelDatabaseHealth.snapshot_at)
    ).limit(1)
    result = await db.execute(stmt)
    latest_snapshot = result.scalar_one_or_none()
    
    # Contar alertas abertos por severidade
    stmt = select(SentinelSystemAlert).where(SentinelSystemAlert.status == "open")
    result = await db.execute(stmt)
    open_alerts = result.scalars().all()
    
    alerts_by_severity = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    for alert in open_alerts:
        if alert.severity in alerts_by_severity:
            alerts_by_severity[alert.severity] += 1
    
    # Parsers não saudáveis
    stmt = select(SentinelParserMetrics).where(SentinelParserMetrics.is_healthy == False)
    result = await db.execute(stmt)
    unhealthy_parsers = result.scalars().all()
    
    # Ingestões falhadas na última hora
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    stmt = select(SentinelIngestionLog).where(
        and_(
            SentinelIngestionLog.status == "failed",
            SentinelIngestionLog.started_at >= one_hour_ago
        )
    )
    result = await db.execute(stmt)
    failed_ingestions = result.scalars().all()
    
    return {
        "overall_status": "healthy" if (latest_snapshot and latest_snapshot.is_healthy and len(unhealthy_parsers) == 0) else "degraded",
        "database_health": {
            "is_healthy": latest_snapshot.is_healthy if latest_snapshot else False,
            "last_check": latest_snapshot.snapshot_at.isoformat() if latest_snapshot else None,
            "issues_count": len(latest_snapshot.health_issues) if (latest_snapshot and latest_snapshot.health_issues) else 0
        },
        "parsers": {
            "total": await db.scalar(select(func.count()).select_from(SentinelParserMetrics)),
            "unhealthy": len(unhealthy_parsers),
            "unhealthy_list": [p.parser_name for p in unhealthy_parsers]
        },
        "alerts": {
            "total_open": len(open_alerts),
            "by_severity": alerts_by_severity
        },
        "ingestion": {
            "failed_last_hour": len(failed_ingestions)
        }
    }
