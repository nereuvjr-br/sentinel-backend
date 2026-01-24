
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.gameplay_v2 import SentinelRaidMinigame
from app.models.notification_v2 import SentinelNotificationLog
from app.models.players_registry_v2 import SentinelPlayerRegistry
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

async def monitor():
    async with AsyncSession(engine) as session:
        print("\n🔎 --- REAL-TIME MONITORING --- 🔎")
        
        # 1. Verify Participants Status
        print("\n[PARTICIPANTS STATUS]")
        players = ['ADM_Sabugador', 'ADM_Mewtwo', 'Minuax']
        for name in players:
            p = (await session.execute(select(SentinelPlayerRegistry).where(SentinelPlayerRegistry.current_name == name))).scalars().first()
            if p:
                print(f"👤 {name:<15} | Tier: {p.plan_tier:<8} | Phone: {p.phone_number} | Exp: {p.plan_expires_at}")
            else:
                print(f"👤 {name:<15} | NOT FOUND")

        # 2. Recent Raids
        print("\n[LATEST 3 RAIDS]")
        raids = (await session.execute(select(SentinelRaidMinigame).order_by(desc(SentinelRaidMinigame.timestamp)).limit(3))).scalars().all()
        for r in raids:
            print(f"⚔️ {r.timestamp.strftime('%H:%M:%S')} | Atk: {r.attacker_name} -> Tgt: {r.target_owner_name} | Success: {r.is_success}")

        # 3. Recent Notifications
        print("\n[LATEST 5 NOTIFICATIONS]")
        notifs = (await session.execute(select(SentinelNotificationLog).order_by(desc(SentinelNotificationLog.sent_at)).limit(5))).scalars().all()
        for n in notifs:
            print(f"📩 {n.sent_at.strftime('%H:%M:%S')} | To: {n.recipient_name} | Status: {n.status} | Err: {n.error_message}")

if __name__ == "__main__":
    asyncio.run(monitor())
