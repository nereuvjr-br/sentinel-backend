import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

async def diagnose_locations():
    # Manually create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        print("Diagnosing Location Data...")
        
        # Count Total
        result = await session.execute(text("SELECT COUNT(*) FROM sentinel_kills"))
        total = result.scalar()
        print(f"Total Kills: {total}")
        
        # Count 0,0
        result = await session.execute(text("SELECT COUNT(*) FROM sentinel_kills WHERE grid_x = 0 AND grid_y = 0"))
        zeros = result.scalar()
        print(f"Kills at 0,0: {zeros}")
        
        # Count Valid
        result = await session.execute(text("SELECT COUNT(*) FROM sentinel_kills WHERE grid_x != 0 OR grid_y != 0"))
        valid = result.scalar()
        print(f"Kills with valid location: {valid}")
        
        # Sample some locations
        print("\nSample Locations (Top 10):")
        result = await session.execute(text("SELECT grid_x, grid_y, COUNT(*) FROM sentinel_kills GROUP BY grid_x, grid_y ORDER BY COUNT(*) DESC LIMIT 10"))
        for row in result:
            print(f"  X={row[0]} Y={row[1]}: {row[2]} kills")

if __name__ == "__main__":
    asyncio.run(diagnose_locations())
