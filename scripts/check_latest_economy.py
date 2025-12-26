import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import engine
from app.models.economy_v2 import SentinelEconomyTrade, SentinelBankTransaction, SentinelMechanicService

async def check_latest_economy():
    async with AsyncSession(engine) as session:
        print("--- Checking Latest Economy Data ---")
        
        # Trades
        stmt = select(SentinelEconomyTrade).order_by(SentinelEconomyTrade.timestamp.desc()).limit(1)
        result = await session.execute(stmt)
        trade = result.scalar_one_or_none()
        if trade:
            print(f"Latest Trade: {trade.timestamp} (UTC) | {trade.player_name} bought/sold {trade.item_class}")
        else:
            print("Latest Trade: None")

        # Bank Transactions
        stmt = select(SentinelBankTransaction).order_by(SentinelBankTransaction.timestamp.desc()).limit(1)
        result = await session.execute(stmt)
        tx = result.scalar_one_or_none()
        if tx:
            print(f"Latest Bank Tx: {tx.timestamp} (UTC) | {tx.player_name} {tx.transaction_type} ${tx.gross_amount}")
        else:
            print("Latest Bank Tx: None")

        # Mechanic Services
        stmt = select(SentinelMechanicService).order_by(SentinelMechanicService.timestamp.desc()).limit(1)
        result = await session.execute(stmt)
        mech = result.scalar_one_or_none()
        if mech:
            print(f"Latest Mechanic Service: {mech.timestamp} (UTC) | {mech.player_name} {mech.service_type} {mech.item_class}")
        else:
            print("Latest Mechanic Service: None")
            
        # Check system time
        result = await session.execute(text("SELECT NOW()"))
        db_time = result.scalar()
        print(f"Database System Time: {db_time}")

if __name__ == "__main__":
    asyncio.run(check_latest_economy())
