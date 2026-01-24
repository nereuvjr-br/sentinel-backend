import asyncio
from datetime import datetime, timedelta
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.core.logger import logger
from app.models.notification_queue import SentinelNotificationQueue
from app.services.evolution_api import evolution_service

class NotificationQueueService:
    def __init__(self):
        self.is_running = False

    async def start_worker(self):
        """Inicia o worker em background."""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("🚀 Notification Queue Worker Started")
        asyncio.create_task(self._worker_loop())

    async def _worker_loop(self):
        """Loop principal de processamento."""
        while self.is_running:
            try:
                await self.process_pending_items()
            except Exception as e:
                logger.error(f"❌ Queue Worker Error: {e}")
            
            await asyncio.sleep(10)  # Check every 10 seconds

    async def process_pending_items(self):
        """Processa itens pendentes que já chegaram no horário."""
        async with AsyncSession(engine, expire_on_commit=False) as session:
            now = datetime.utcnow()
            
            # Buscar itens pendentes
            stmt = select(SentinelNotificationQueue).where(
                SentinelNotificationQueue.status == "pending",
                SentinelNotificationQueue.scheduled_for <= now
            ).limit(20)  # Process in batches
            
            result = await session.execute(stmt)
            items = result.scalars().all()
            
            if not items:
                return

            logger.info(f"📬 Processing {len(items)} queued notifications...")
            
            for item in items:
                try:
                    # Enviar via Evolution API
                    success = await evolution_service.send_message(item.recipient_phone, item.message_content)
                    
                    if success:
                        item.status = "processed"
                        item.processed_at = datetime.utcnow()
                        logger.info(f"✅ Queued Item {item.id} sent to {item.recipient_phone}")
                    else:
                        item.status = "failed" # Retry logic could go here
                        item.error_message = "Evolution API Failed"
                        logger.warning(f"⚠️ Queued Item {item.id} failed to send.")
                        
                except Exception as e:
                    item.status = "failed"
                    item.error_message = str(e)
                    logger.error(f"❌ Error processing item {item.id}: {e}")
                
                session.add(item)
            
            await session.commit()

    async def enqueue_notification(self, recipient_phone: str, message: str, delay_minutes: int, metadata: dict = None):
        """Adiciona uma notificação à fila."""
        scheduled_for = datetime.utcnow() + timedelta(minutes=delay_minutes)
        
        async with AsyncSession(engine) as session:
            item = SentinelNotificationQueue(
                recipient_phone=recipient_phone,
                message_content=message,
                scheduled_for=scheduled_for,
                event_metadata=metadata,
                status="pending"
            )
            session.add(item)
            await session.commit()
            
        logger.info(f"⏳ Notification queued for {recipient_phone} in {delay_minutes}min")

notification_queue = NotificationQueueService()
