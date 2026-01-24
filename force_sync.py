import asyncio
import logging
from app.services.scum_db_service import scum_db_service

# Setup logging to console
logging.basicConfig(level=logging.INFO)

async def main():
    print("🚀 Forcing SCUM.db Sync...")
    
    # Run the sync routine
    # This will download SCUM.db, extract data, and update Postgres
    await scum_db_service.sync_routine()
    
    print("✅ Sync finished. Check logs/terminal for 'Name change detected'.")

if __name__ == "__main__":
    asyncio.run(main())
