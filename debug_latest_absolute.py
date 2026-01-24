
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.gameplay_v2 import SentinelRaidMinigame
from app.models.notification_v2 import SentinelNotificationLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

async def check_latest_activity():
    async with AsyncSession(engine) as session:
        print("--- CHECKING LATEST ACTIVITY (Last 5 mins) ---")
        
        # Latest Raids
        print("\n[LATEST RAIDS]")
        raids = (await session.execute(select(SentinelRaidMinigame).order_by(desc(SentinelRaidMinigame.timestamp)).limit(5))).scalars().all()
        for r in raids:
            print(f"⚔️ ID:{r.id} | Time:{r.timestamp} | Atk: {r.attacker_name} | Success: {r.is_success} | Target: {r.target_owner_name}")

        # Latest Notifs
        print("\n[LATEST NOTIFICATIONS]")
        notifs = (await session.execute(select(SentinelNotificationLog).order_by(desc(SentinelNotificationLog.sent_at)).limit(5))).scalars().all()
        for n in notifs:
            print(f"📩 ID:{n.id} | Time:{n.sent_at.strftime('%H:%M:%S')} | To: {n.recipient_name} | Status: {n.status} | Err: {n.error_message}")

if __name__ == "__main__":
    asyncio.run(check_latest_activity())
