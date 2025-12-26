import asyncio
import logging
from datetime import datetime, timezone
from sqlmodel import select, col, func
from app.core.config import settings
from app.core.database import engine
from app.models.kill_v2 import SentinelKill
from app.models.login_v2 import SentinelLogin
from app.models.chat_v2 import SentinelChatMessage
from app.models.economy_v2 import SentinelEconomyTrade
from sqlalchemy.ext.asyncio import AsyncSession

# Silence SQL Logs
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

async def main():
    if not settings.WIPE_DATE:
        print("⚠️ WIPE_DATE not set in settings.")
        return

    wipe_date_str = settings.WIPE_DATE
    print(f"Checking compliance for WIPE_DATE: {wipe_date_str}")
    
    # Simple parse for display, the parser uses robust logic but we can rely on SQL comparison
    # Ideally we should convert WIPE_DATE to the same UTC naive/aware format stored in DB
    # The DB stores Naive UTC.
    
    # We will just query the MIN(timestamp) from tables and compare manually
    
    tables = {
        "Kills": SentinelKill,
        "Logins": SentinelLogin,
        "Chat": SentinelChatMessage,
        "Economy": SentinelEconomyTrade
    }
    
    async with AsyncSession(engine) as session:
        for name, model in tables.items():
            try:
                stmt = select(func.min(model.timestamp))
                result = await session.execute(stmt)
                min_ts = result.scalar()
                
                if min_ts:
                    print(f"[{name}] Oldest Record: {min_ts}")
                else:
                    print(f"[{name}] No records found.")
            except Exception as e:
                print(f"[{name}] Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
