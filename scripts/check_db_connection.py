import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def check_connection():
    # Parse original URL
    original_url = settings.DATABASE_URL
    
    # Replace hostname with IP provided by user for testing
    # Assuming standard format: postgresql://user:pass@HOST:PORT/db
    if "@" in original_url:
        prefix, suffix = original_url.split("@", 1)
        # Suffix is host:port/db
        remaining_parts = suffix.split("/", 1) # host:port, db...
        if len(remaining_parts) == 2:
            host_port, db_name = remaining_parts
            # Force new host
            new_host = "159.65.174.208:5432"
            test_url = f"{prefix}@{new_host}/{db_name}"
        else:
            print("Could not parse URL suffix correctly")
            test_url = original_url
    else:
        test_url = original_url

    print(f"Testing connection to: 159.65.174.208 (Overridden)")
    
    # Force asyncpg
    if test_url.startswith("postgresql://"):
        test_url = test_url.replace("postgresql://", "postgresql+asyncpg://")

    try:
        engine = create_async_engine(test_url)
        print("Engine created. Connecting...")
        async with engine.connect() as conn:
            print("Connection established. Executing query...")
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            print(f"Result: {result.scalar()}")
        await engine.dispose()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Database connection FAILED")
        print(f"Type: {type(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(check_connection())
