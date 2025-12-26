from sqlmodel import select, func
from app.core.database import engine
from app.models.admin_v2 import SentinelAdminCommand
from app.models.chat_v2 import SentinelChatMessage
from app.models.login_v2 import SentinelLogin
from app.models.kill_v2 import SentinelKill
from app.models.economy_v2 import SentinelEconomyTrade, SentinelEconomyBalance
from app.models.gameplay_v2 import SentinelRaidMinigame, SentinelCrafting, SentinelExplosiveEvent, SentinelBunkerEvent
from app.models.violation_v2 import SentinelViolation
from app.models.chest_fame_v2 import SentinelChestEvent, SentinelFameEvent
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

async def count_rows():
    print("📊 Monitor de Ingestão Sentinel V2")
    print("-" * 30)
    
    models = [
        ("Admin Commands", SentinelAdminCommand),
        ("Chat Messages", SentinelChatMessage),
        ("Logins", SentinelLogin),
        ("Kills", SentinelKill),
        ("Trades", SentinelEconomyTrade),
        ("Balances", SentinelEconomyBalance),
        ("Raids", SentinelRaidMinigame),
        ("Crafting", SentinelCrafting),
        ("Explosives", SentinelExplosiveEvent),
        ("Bunkers", SentinelBunkerEvent),
        ("Violations", SentinelViolation),
        ("Chest Events", SentinelChestEvent),
        ("Fame Events", SentinelFameEvent)
    ]
    
    async with AsyncSession(engine) as session:
        total = 0
        for name, model in models:
            stmt = select(func.count()).select_from(model)
            result = await session.execute(stmt)
            count = result.scalar()
            print(f"{name:<20}: {count}")
            total += count
            
        print("-" * 30)
        print(f"Total Rows Processed: {total}")

if __name__ == "__main__":
    asyncio.run(count_rows())
