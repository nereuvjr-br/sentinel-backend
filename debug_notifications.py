
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.notification_v2 import SentinelNotificationLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

async def check():
    async with AsyncSession(engine) as session:
        print("\n--- Checking Recent Notifications (Last 10) ---")
        q3 = select(SentinelNotificationLog).order_by(desc(SentinelNotificationLog.sent_at)).limit(10)
        res3 = await session.execute(q3)
        notifs = res3.scalars().all()
        for n in notifs:
            print(f"Notif: {n.sent_at} | To: {n.recipient_name} | Type: {n.notification_type} | Status: {n.status} | Err: {n.error_message}")
            
if __name__ == "__main__":
    asyncio.run(check())
