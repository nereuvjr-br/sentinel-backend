
import asyncio
import time
from sqlmodel import select
from app.core.database import engine
from app.models.gameplay_v2 import SentinelRaidMinigame
from app.models.notification_v2 import SentinelNotificationLog
from app.models.players_registry_v2 import SentinelPlayerRegistry
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

async def monitor_loop():
    print("🔎 --- STARTED 60s MONITORING --- 🔎")
    
    last_raid_id = 0
    last_notif_id = 0
    
    # Get initial max IDs to avoid printing old stuff
    async with AsyncSession(engine) as session:
        r = (await session.execute(select(SentinelRaidMinigame).order_by(desc(SentinelRaidMinigame.id)).limit(1))).scalars().first()
        if r: last_raid_id = r.id
        
        n = (await session.execute(select(SentinelNotificationLog).order_by(desc(SentinelNotificationLog.id)).limit(1))).scalars().first()
        if n: last_notif_id = n.id

    for i in range(60): # 60 * 5s = 300s (5 min)
        async with AsyncSession(engine) as session:
            # Check Raids
            new_raids = (await session.execute(select(SentinelRaidMinigame).where(SentinelRaidMinigame.id > last_raid_id).order_by(SentinelRaidMinigame.timestamp))).scalars().all()
            for r in new_raids:
                print(f"⚔️ [NEW RAID] {r.timestamp.strftime('%H:%M:%S')} | Atk: {r.attacker_name} -> Tgt: {r.target_owner_name} | Success: {r.is_success}")
                if r.id > last_raid_id: last_raid_id = r.id
            
            # Check Notifs
            new_notifs = (await session.execute(select(SentinelNotificationLog).where(SentinelNotificationLog.id > last_notif_id).order_by(SentinelNotificationLog.sent_at))).scalars().all()
            for n in new_notifs:
                print(f"📩 [NEW NOTIF] {n.sent_at.strftime('%H:%M:%S')} | To: {n.recipient_name} | Status: {n.status} | Err: {n.error_message}")
                if n.id > last_notif_id: last_notif_id = n.id
                
        await asyncio.sleep(5)
        # print(f".", end="", flush=True)

    print("\n🏁 --- MONITORING FINISHED ---")

if __name__ == "__main__":
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        pass
