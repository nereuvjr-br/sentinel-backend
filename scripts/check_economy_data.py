import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def check_economy_data():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        # Verificar dados de economia
        print("\n📊 VERIFICANDO DADOS DE ECONOMIA:\n")
        
        # Trades
        result = await conn.execute(text("SELECT COUNT(*) FROM sentinel_economy_trades"))
        trades_count = result.scalar()
        print(f"✅ Trades: {trades_count:,}")
        
        # Balances
        result = await conn.execute(text("SELECT COUNT(*) FROM sentinel_economy_balances"))
        balances_count = result.scalar()
        print(f"✅ Balances: {balances_count:,}")
        
        # Bank Transactions
        result = await conn.execute(text("SELECT COUNT(*) FROM sentinel_bank_transactions"))
        bank_count = result.scalar()
        print(f"✅ Bank Transactions: {bank_count:,}")
        
        # Últimos 5 balances
        if balances_count > 0:
            print("\n📋 ÚLTIMOS 5 BALANCES:")
            result = await conn.execute(text("""
                SELECT steam_id, cash, bank, gold, timestamp 
                FROM sentinel_economy_balances 
                ORDER BY timestamp DESC 
                LIMIT 5
            """))
            rows = result.fetchall()
            for row in rows:
                print(f"  {row[0]}: Cash=${row[1]:,} Bank=${row[2]:,} Gold={row[3]:,}g @ {row[4]}")
        
        # Verificar se há dados únicos de steam_id
        result = await conn.execute(text("""
            SELECT COUNT(DISTINCT steam_id) 
            FROM sentinel_economy_balances
        """))
        unique_players = result.scalar()
        print(f"\n👥 Jogadores únicos com balances: {unique_players:,}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_economy_data())
