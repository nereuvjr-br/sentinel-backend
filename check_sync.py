import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_counts():
    async with engine.connect() as conn:
        print("Checking DB counts...")
        res_clans = await conn.execute(text("SELECT count(*) FROM sentinel_clans"))
        res_players = await conn.execute(text("SELECT count(*) FROM sentinel_players_registry"))
        
        print(f"Clans Count: {res_clans.scalar()}")
        print(f"Players Count: {res_players.scalar()}")

if __name__ == "__main__":
    asyncio.run(check_counts())
