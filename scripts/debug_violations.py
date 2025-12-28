
import asyncio
from sqlalchemy import text, select
from app.core.database import engine
from app.models.system_v2 import SentinelProcessedFile
from sqlalchemy.ext.asyncio import AsyncSession

async def debug_violations():
    async with AsyncSession(engine) as session:
        # 1. Count Violations
        res = await session.execute(text("SELECT COUNT(*) FROM sentinel_violations"))
        count = res.scalar()
        print(f"COUNT sentinel_violations: {count}")
        
        # 2. Check Processed Files related to violations
        stmt = select(SentinelProcessedFile).where(SentinelProcessedFile.filename.ilike("%violation%"))
        res = await session.execute(stmt)
        files = res.scalars().all()
        
        print("\n--- Processed Files (Violations) ---")
        if not files:
            print("Nenhum arquivo de violations encontrado em sentinel_processed_files!")
        for f in files:
            print(f"File: {f.filename} | Type: {f.log_type} | Lines: {f.lines_processed} | Bytes: {f.processed_bytes}")

        # 3. Check Unparsed related to violations
        res = await session.execute(text("SELECT COUNT(*) FROM sentinel_unparsed_logs WHERE filename LIKE '%violation%'"))
        unparsed_count = res.scalar()
        print(f"\nCOUNT sentinel_unparsed_logs (violation files): {unparsed_count}")

if __name__ == "__main__":
    asyncio.run(debug_violations())
