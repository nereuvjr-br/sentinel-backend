"""
Script para popular sentinel_player_wallets a partir de sentinel_economy_balances
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

async def populate_player_wallets():
    print("🔄 Populando sentinel_player_wallets...\n")
    
    async with AsyncSession(engine) as session:
        # Limpar tabela primeiro
        print("1. Limpando tabela antiga...")
        await session.execute(text("TRUNCATE TABLE sentinel_player_wallets"))
        await session.commit()
        print("   ✅ Tabela limpa\n")
        
        # Popular com dados mais recentes de cada jogador
        print("2. Inserindo dados...")
        query = text("""
            INSERT INTO sentinel_player_wallets 
            (steam_id, player_name, cash, bank, gold, net_worth, total_earned, total_spent, squad_name, last_transaction)
            SELECT DISTINCT ON (steam_id)
                steam_id,
                player_name,
                COALESCE(cash, 0) as cash,
                COALESCE(bank, 0) as bank,
                COALESCE(gold, 0) as gold,
                COALESCE(cash, 0) + COALESCE(bank, 0) + COALESCE(gold, 0) as net_worth,
                0 as total_earned,  -- TODO: calcular do histórico
                0 as total_spent,   -- TODO: calcular do histórico
                NULL as squad_name, -- TODO: extrair do nome
                timestamp as last_transaction
            FROM sentinel_economy_balances
            ORDER BY steam_id, timestamp DESC
        """)
        
        result = await session.execute(query)
        await session.commit()
        
        # Verificar quantos foram inseridos
        count_result = await session.execute(text("SELECT COUNT(*) FROM sentinel_player_wallets"))
        count = count_result.scalar()
        
        print(f"   ✅ {count} jogadores inseridos\n")
        
        # Mostrar top 5
        print("3. Top 5 jogadores mais ricos:")
        top_result = await session.execute(text("""
            SELECT player_name, cash, bank, gold, net_worth 
            FROM sentinel_player_wallets 
            ORDER BY net_worth DESC 
            LIMIT 5
        """))
        
        for idx, row in enumerate(top_result.fetchall(), 1):
            print(f"   {idx}. {row[0]:30} - Net Worth: ${row[4]:,}")
            print(f"      Cash: ${row[1]:,} | Bank: ${row[2]:,} | Gold: {row[3]:,}g")
        
        print("\n✅ sentinel_player_wallets populada com sucesso!")

if __name__ == "__main__":
    asyncio.run(populate_player_wallets())
