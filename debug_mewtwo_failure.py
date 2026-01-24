
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.notification_v2 import SentinelNotificationLog
from app.models.players_registry_v2 import SentinelPlayerRegistry
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

async def check_mewtwo_notif():
    async with AsyncSession(engine) as session:
        print("--- Checking ADM_Mewtwo Status & Logs ---")
        
        # 1. Verify Current Tier in DB
        p = (await session.execute(select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.current_name == 'ADM_Mewtwo'))).scalars().first()
        if p:
            print(f"👤 Player: {p.current_name}")
            print(f"   Tier: {p.plan_tier}")
            print(f"   Expires: {p.plan_expires_at}")
        
        # 2. Check Last 5 Notifications for him
        print("\n--- Last 5 Notifications for ADM_Mewtwo ---")
        q = select(SentinelNotificationLog).where(SentinelNotificationLog.recipient_name.contains("Mewtwo")).order_by(desc(SentinelNotificationLog.sent_at)).limit(5)
        res = await session.execute(q)
        notifs = res.scalars().all()
        
        for n in notifs:
            print(f"📩 Time: {n.sent_at} | Status: {n.status}")
            print(f"   Error: {n.error_message}")
            print(f"   Type: {n.notification_type}")
            print(f"   Context: {n.event_context}")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(check_mewtwo_notif())
