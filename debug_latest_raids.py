
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.gameplay_v2 import SentinelRaidMinigame
from app.models.notification_v2 import SentinelNotificationLog
from app.models.economy_v2 import SentinelUnparsedLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

async def check():
    async with AsyncSession(engine) as session:
        print("--- Checking Recent Raid Events (Last 5) ---")
        q = select(SentinelRaidMinigame).order_by(desc(SentinelRaidMinigame.timestamp)).limit(5)
        res = await session.execute(q)
        raids = res.scalars().all()
        for r in raids:
            print(f"Raid: {r.timestamp} | Attacker: {r.attacker_name} | Target: {r.target_owner_name} (Steam: {r.target_owner_steam_id}) | Success: {r.is_success}")
        if not raids:
            print("No recent raid events found.")

        print("\n--- Checking Recent Unparsed Gameplay Logs (Last 5) ---")
        q2 = select(SentinelUnparsedLog).where(SentinelUnparsedLog.log_type == "Gameplay").order_by(desc(SentinelUnparsedLog.created_at)).limit(5)
        res2 = await session.execute(q2)
        unparsed = res2.scalars().all()
        for u in unparsed:
            print(f"Unparsed: {u.created_at} | Error: {u.error_message} | Line: {u.raw_line[:100]}...")
        if not unparsed:
            print("No recent unparsed gameplay logs found.")
            
        print("\n--- Checking Recent Notifications (Last 5) ---")
        q3 = select(SentinelNotificationLog).order_by(desc(SentinelNotificationLog.sent_at)).limit(5)
        res3 = await session.execute(q3)
        notifs = res3.scalars().all()
        for n in notifs:
            print(f"Notif: {n.sent_at} | To: {n.recipient_name} | Type: {n.notification_type} | Status: {n.status}")

if __name__ == "__main__":
    asyncio.run(check())
