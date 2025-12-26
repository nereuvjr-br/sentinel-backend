import asyncio
import logging
from sqlmodel import select, func
# Silence SQL Logs
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from app.core.database import engine
from app.models.kill_v2 import SentinelKill
from app.models.login_v2 import SentinelLogin
from app.models.chat_v2 import SentinelChatMessage
from app.models.admin_v2 import SentinelAdminCommand
from app.models.system_v2 import SentinelProcessedFile
from app.models.economy_v2 import SentinelEconomyTrade
from sqlalchemy.ext.asyncio import AsyncSession

async def main():
    async with AsyncSession(engine) as session:
        print("--- Database Row Counts ---")
        
        counts = {
            "Processed Files": SentinelProcessedFile,
            "Kills": SentinelKill,
            "Logins": SentinelLogin,
            "Chat Messages": SentinelChatMessage,
            "Admin Commands": SentinelAdminCommand,
            "Economy Trades": SentinelEconomyTrade
        }
        
        for name, model in counts.items():
            try:
                stmt = select(func.count()).select_from(model)
                result = await session.execute(stmt)
                count = result.scalar()
                print(f"{name}: {count}")
            except Exception as e:
                print(f"{name}: Error ({e}) - Table might not exist yet")

if __name__ == "__main__":
    asyncio.run(main())
