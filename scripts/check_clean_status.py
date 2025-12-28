
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Silenciar logs para output limpo
logging.basicConfig(level=logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

async def check_clean():
    tables = [
        "sentinel_kills", "sentinel_logins", "sentinel_chat_messages", 
        "sentinel_admin_commands", "sentinel_economy_trades", 
        "sentinel_economy_balances", "sentinel_bank_transactions", 
        "sentinel_mechanic_services", "sentinel_bank_cards",
        "sentinel_processed_files"
    ]
    
    print(f"{'TABELA':<30} | {'COUNT':<10}")
    print("-" * 45)
    
    async with AsyncSession(engine) as session:
        for t in tables:
            try:
                res = await session.execute(text(f"SELECT COUNT(*) FROM {t}"))
                count = res.scalar()
                status = "✅ ZERADA" if count == 0 else f"❌ {count} REGISTROS"
                print(f"{t:<30} | {count:<10} {status}")
            except Exception as e:
                print(f"{t:<30} | ERRO: {e}")

if __name__ == "__main__":
    asyncio.run(check_clean())
