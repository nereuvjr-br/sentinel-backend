import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monitoring_v2 import (
    SentinelParserMetrics,
    SentinelDatabaseHealth,
    SentinelIngestionLog,
    SentinelSystemAlert
)
from app.models.admin_v2 import SentinelAdminCommand
from app.models.chat_v2 import SentinelChatMessage
from app.models.login_v2 import SentinelLogin
from app.models.kill_v2 import SentinelKill
from app.models.economy_v2 import (
    SentinelEconomyTrade,
    SentinelEconomyBalance,
    SentinelBankTransaction,
    SentinelMechanicService,
    SentinelBankCard,
    SentinelUnparsedLog
    # SentinelPlayerWallet,
    # SentinelItemEconomy,
    # SentinelEconomyAlert,
    # SentinelTraderInventory,
    # SentinelAccountRegistry
)
from app.models.gameplay_v2 import SentinelRaidMinigame, SentinelCrafting
from app.models.chest_fame_v2 import SentinelChestEvent, SentinelFameEvent
from app.models.vehicle_v2 import SentinelVehicle
from app.models.violation_v2 import SentinelViolation
from app.models.system_v2 import SentinelProcessedFile

from app.core.logger import logger


class MonitoringService:
    """
    Serviço centralizado de monitoramento do Sentinel.
    Rastreia métricas de parsers, saúde do banco e gera alertas.
    """
    
    def __init__(self):
        self.parser_names = [
            "Admin", "Chat", "Login", "Kill", "Economy", 
            "Gameplay", "Violation", "Chest", "Fame", "Vehicle"
        ]
    
    async def update_parser_metrics(
        self,
        session: AsyncSession,
        parser_name: str,
        lines_processed: int,
        lines_success: int,
        lines_failed: int,
        processing_time_ms: float,
        last_error: Optional[str] = None
    ):
        """
        Atualiza as métricas de um parser específico.
        """
        # Buscar ou criar métrica
        stmt = select(SentinelParserMetrics).where(
            SentinelParserMetrics.parser_name == parser_name
        )
        result = await session.execute(stmt)
        metric = result.scalar_one_or_none()
        
        if not metric:
            metric = SentinelParserMetrics(parser_name=parser_name)
        
        # Atualizar contadores
        metric.total_lines_processed += lines_processed
        metric.total_lines_success += lines_success
        metric.total_lines_failed += lines_failed
        
        # Calcular taxa de sucesso
        if metric.total_lines_processed > 0:
            metric.success_rate = (metric.total_lines_success / metric.total_lines_processed) * 100
        
        # Atualizar performance
        metric.last_batch_size = lines_processed
        metric.last_batch_time_ms = processing_time_ms
        
        if lines_processed > 0:
            metric.avg_parse_time_ms = processing_time_ms / lines_processed
        
        # Status de saúde
        metric.is_healthy = metric.success_rate >= 95.0  # Threshold: 95%
        
        if last_error:
            metric.last_error = last_error
            metric.error_count_last_hour += 1
        
        metric.last_processed_at = datetime.utcnow()
        metric.updated_at = datetime.utcnow()
        
        session.add(metric)
        await session.commit()
        
        # Gerar alerta se não estiver saudável
        if not metric.is_healthy:
            await self._create_alert(
                session,
                alert_type="parser_degraded",
                severity="high" if metric.success_rate < 80 else "medium",
                component=parser_name,
                title=f"Parser {parser_name} com baixa taxa de sucesso",
                description=f"Taxa de sucesso: {metric.success_rate:.2f}%",
                evidence={
                    "success_rate": metric.success_rate,
                    "total_processed": metric.total_lines_processed,
                    "total_failed": metric.total_lines_failed,
                    "last_error": metric.last_error
                }
            )
    
    async def log_ingestion_cycle(
        self,
        session: AsyncSession,
        filename: str,
        log_type: str,
        bytes_processed: int,
        lines_processed: int,
        lines_success: int,
        lines_failed: int,
        processing_time_ms: float,
        offset_start: int,
        offset_end: int,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """
        Registra um ciclo completo de ingestão de arquivo.
        """
        throughput = 0.0
        if processing_time_ms > 0:
            throughput = (lines_processed / processing_time_ms) * 1000  # linhas/segundo
        
        log_entry = SentinelIngestionLog(
            filename=filename,
            log_type=log_type,
            bytes_processed=bytes_processed,
            lines_processed=lines_processed,
            lines_success=lines_success,
            lines_failed=lines_failed,
            processing_time_ms=processing_time_ms,
            throughput_lines_per_sec=throughput,
            status=status,
            error_message=error_message,
            offset_start=offset_start,
            offset_end=offset_end,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        session.add(log_entry)
        await session.commit()
        
        logger.info(
            f"📊 Ingestão: {filename} | "
            f"{lines_processed} linhas | "
            f"{throughput:.2f} linhas/s | "
            f"Status: {status}"
        )
    
    async def capture_database_health_snapshot(self, session: AsyncSession):
        """
        Captura um snapshot completo da saúde do banco de dados.
        """
        snapshot = SentinelDatabaseHealth()
        
        # Contar registros em cada tabela
        snapshot.count_admin_commands = await self._count_table(session, SentinelAdminCommand)
        snapshot.count_chat_messages = await self._count_table(session, SentinelChatMessage)
        snapshot.count_logins = await self._count_table(session, SentinelLogin)
        snapshot.count_kills = await self._count_table(session, SentinelKill)
        
        snapshot.count_economy_trades = await self._count_table(session, SentinelEconomyTrade)
        snapshot.count_economy_balances = await self._count_table(session, SentinelEconomyBalance)
        snapshot.count_bank_transactions = await self._count_table(session, SentinelBankTransaction)
        snapshot.count_mechanic_services = await self._count_table(session, SentinelMechanicService)
        snapshot.count_bank_cards = await self._count_table(session, SentinelBankCard)
        
        snapshot.count_raids = await self._count_table(session, SentinelRaidMinigame)
        snapshot.count_crafting = await self._count_table(session, SentinelCrafting)
        snapshot.count_chest_events = await self._count_table(session, SentinelChestEvent)
        snapshot.count_fame_events = await self._count_table(session, SentinelFameEvent)
        
        snapshot.count_violations = await self._count_table(session, SentinelViolation)
        snapshot.count_vehicles = await self._count_table(session, SentinelVehicle)
        snapshot.count_unparsed_logs = await self._count_table(session, SentinelUnparsedLog)
        snapshot.count_processed_files = await self._count_table(session, SentinelProcessedFile)
        
        # Tabelas de análise agregada (comentadas pois não existem ainda)
        snapshot.count_player_wallets = 0  # await self._count_table(session, SentinelPlayerWallet)
        snapshot.count_item_economy = 0  # await self._count_table(session, SentinelItemEconomy)
        snapshot.count_economy_alerts = 0  # await self._count_table(session, SentinelEconomyAlert)
        snapshot.count_trader_inventory = 0  # await self._count_table(session, SentinelTraderInventory)
        snapshot.count_account_registry = 0  # await self._count_table(session, SentinelAccountRegistry)
        
        # Calcular taxas de crescimento (comparar com snapshot anterior)
        previous_snapshot = await self._get_previous_snapshot(session)
        if previous_snapshot:
            time_diff = (datetime.utcnow() - previous_snapshot.snapshot_at).total_seconds() / 60  # minutos
            
            if time_diff > 0:
                snapshot.growth_rate_kills = (snapshot.count_kills - previous_snapshot.count_kills) / time_diff
                snapshot.growth_rate_trades = (snapshot.count_economy_trades - previous_snapshot.count_economy_trades) / time_diff
                snapshot.growth_rate_logins = (snapshot.count_logins - previous_snapshot.count_logins) / time_diff
        
        # Detectar problemas
        health_issues = []
        
        # Verificar se há muitos logs não parseados
        if snapshot.count_unparsed_logs > 1000:
            health_issues.append({
                "type": "high_unparsed_count",
                "severity": "medium",
                "message": f"{snapshot.count_unparsed_logs} logs não parseados"
            })
        
        # Verificar se há crescimento zero (sistema parado?)
        if previous_snapshot and time_diff > 10:  # Mais de 10 minutos
            if (snapshot.growth_rate_kills == 0 and 
                snapshot.growth_rate_trades == 0 and 
                snapshot.growth_rate_logins == 0):
                health_issues.append({
                    "type": "no_growth_detected",
                    "severity": "high",
                    "message": "Nenhum crescimento detectado nos últimos 10 minutos"
                })
        
        snapshot.is_healthy = len(health_issues) == 0
        snapshot.health_issues = health_issues if health_issues else None
        
        session.add(snapshot)
        await session.commit()
        
        logger.info(f"📸 Snapshot de Saúde: {len(health_issues)} problemas detectados")
        
        return snapshot
    
    async def get_system_health_report(self, session: AsyncSession) -> Dict:
        """
        Gera um relatório completo de saúde do sistema.
        """
        # Buscar última snapshot
        snapshot = await self._get_latest_snapshot(session)
        
        # Buscar métricas de todos os parsers
        stmt = select(SentinelParserMetrics)
        result = await session.execute(stmt)
        parser_metrics = result.scalars().all()
        
        # Buscar alertas abertos
        stmt = select(SentinelSystemAlert).where(
            SentinelSystemAlert.status == "open"
        ).order_by(SentinelSystemAlert.detected_at.desc())
        result = await session.execute(stmt)
        open_alerts = result.scalars().all()
        
        # Buscar logs de ingestão recentes (última hora)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        stmt = select(SentinelIngestionLog).where(
            SentinelIngestionLog.started_at >= one_hour_ago
        ).order_by(SentinelIngestionLog.started_at.desc())
        result = await session.execute(stmt)
        recent_ingestions = result.scalars().all()
        
        # Compilar relatório
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": "healthy" if (snapshot and snapshot.is_healthy) else "degraded",
            "database_snapshot": {
                "total_records": self._sum_snapshot_counts(snapshot) if snapshot else 0,
                "growth_rates": {
                    "kills_per_min": snapshot.growth_rate_kills if snapshot else 0,
                    "trades_per_min": snapshot.growth_rate_trades if snapshot else 0,
                    "logins_per_min": snapshot.growth_rate_logins if snapshot else 0
                },
                "issues": snapshot.health_issues if snapshot else []
            },
            "parsers": [
                {
                    "name": m.parser_name,
                    "is_healthy": m.is_healthy,
                    "success_rate": m.success_rate,
                    "total_processed": m.total_lines_processed,
                    "total_failed": m.total_lines_failed,
                    "last_processed": m.last_processed_at.isoformat() if m.last_processed_at else None,
                    "avg_parse_time_ms": m.avg_parse_time_ms
                }
                for m in parser_metrics
            ],
            "alerts": [
                {
                    "id": a.id,
                    "type": a.alert_type,
                    "severity": a.severity,
                    "component": a.component,
                    "title": a.title,
                    "description": a.description,
                    "detected_at": a.detected_at.isoformat()
                }
                for a in open_alerts
            ],
            "recent_ingestions": [
                {
                    "filename": log.filename,
                    "log_type": log.log_type,
                    "lines_processed": log.lines_processed,
                    "throughput": log.throughput_lines_per_sec,
                    "status": log.status,
                    "started_at": log.started_at.isoformat()
                }
                for log in recent_ingestions[:10]  # Últimos 10
            ]
        }
        
        return report
    
    async def _count_table(self, session: AsyncSession, model) -> int:
        """Helper para contar registros em uma tabela."""
        try:
            stmt = select(func.count()).select_from(model)
            result = await session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Erro ao contar tabela {model.__tablename__}: {e}")
            return 0
    
    async def _get_previous_snapshot(self, session: AsyncSession) -> Optional[SentinelDatabaseHealth]:
        """Busca o snapshot anterior para calcular taxas de crescimento."""
        stmt = select(SentinelDatabaseHealth).order_by(
            SentinelDatabaseHealth.snapshot_at.desc()
        ).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_latest_snapshot(self, session: AsyncSession) -> Optional[SentinelDatabaseHealth]:
        """Busca o snapshot mais recente."""
        stmt = select(SentinelDatabaseHealth).order_by(
            SentinelDatabaseHealth.snapshot_at.desc()
        ).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    def _sum_snapshot_counts(self, snapshot: SentinelDatabaseHealth) -> int:
        """Soma todos os contadores de um snapshot."""
        return (
            snapshot.count_admin_commands +
            snapshot.count_chat_messages +
            snapshot.count_logins +
            snapshot.count_kills +
            snapshot.count_economy_trades +
            snapshot.count_economy_balances +
            snapshot.count_bank_transactions +
            snapshot.count_mechanic_services +
            snapshot.count_bank_cards +
            snapshot.count_raids +
            snapshot.count_crafting +
            snapshot.count_chest_events +
            snapshot.count_fame_events +
            snapshot.count_violations +
            snapshot.count_vehicles
        )
    
    async def _create_alert(
        self,
        session: AsyncSession,
        alert_type: str,
        severity: str,
        component: str,
        title: str,
        description: str,
        evidence: Optional[Dict] = None
    ):
        """Cria um novo alerta se não existir um similar aberto."""
        # Verificar se já existe alerta similar aberto
        stmt = select(SentinelSystemAlert).where(
            and_(
                SentinelSystemAlert.alert_type == alert_type,
                SentinelSystemAlert.component == component,
                SentinelSystemAlert.status == "open"
            )
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Atualizar alerta existente
            existing.description = description
            existing.evidence = evidence
            existing.detected_at = datetime.utcnow()
            session.add(existing)
        else:
            # Criar novo alerta
            alert = SentinelSystemAlert(
                alert_type=alert_type,
                severity=severity,
                component=component,
                title=title,
                description=description,
                evidence=evidence
            )
            session.add(alert)
        
        await session.commit()
        logger.warning(f"🚨 Alerta: [{severity.upper()}] {title} - {description}")


# Singleton
monitoring_service = MonitoringService()
