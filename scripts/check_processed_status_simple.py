
import asyncio
import sys
sys.path.insert(0, '/home/nereu-jr/Área de trabalho/scum/SCUMSentinel/backend')
from app.core.database import engine
from sqlalchemy import text

async def check_status():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT filename, processed_bytes, lines_processed FROM sentinel_processed_files WHERE log_type = 'Economy' ORDER BY filename DESC LIMIT 10"))
        rows = result.fetchall()
        print("filename | processed_bytes | lines_processed")
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]}")

if __name__ == "__main__":
    asyncio.run(check_status())
