import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def check_wallets():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("SELECT COUNT(*) FROM sentinel_player_wallets"))
            count = result.scalar()
            print(f"✅ Wallets: {count:,}")
        except Exception as e:
            print(f"❌ Erro ao buscar wallets: {e}")
            print("\n🔍 Verificando se a tabela existe...")
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'sentinel_player_wallets'
            """))
            exists = result.fetchone()
            if not exists:
                print("❌ A tabela 'sentinel_player_wallets' NÃO EXISTE!")
            else:
                print("✅ A tabela existe, mas há outro erro")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_wallets())
