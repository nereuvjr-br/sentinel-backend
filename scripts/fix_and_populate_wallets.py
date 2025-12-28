"""
Script para adicionar colunas faltantes em sentinel_player_wallets e popular dados
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def upgrade_and_populate():
    print("🔄 Atualizando e populando sentinel_player_wallets...\n")
    
    async with AsyncSession(engine) as session:
        # 1. Adicionar colunas se não existirem
        print("1. Verificando/Adicionando colunas...")
        try:
            await session.execute(text("ALTER TABLE sentinel_player_wallets ADD COLUMN IF NOT EXISTS net_worth DOUBLE PRECISION DEFAULT 0"))
            await session.execute(text("ALTER TABLE sentinel_player_wallets ADD COLUMN IF NOT EXISTS squad_name VARCHAR(255)"))
            await session.commit()
            print("   ✅ Colunas net_worth e squad_name verificadas/adicionadas\n")
        except Exception as e:
            print(f"   ⚠️ Erro ao alterar tabela (pode já existir): {e}\n")
            await session.rollback()

        # 2. Limpar tabela
        print("2. Limpando dados antigos...")
        await session.execute(text("TRUNCATE TABLE sentinel_player_wallets"))
        await session.commit()
        print("   ✅ Tabela limpa\n")
        
        # 3. Popular com dados
        print("3. Inserindo dados de balances...")
        # Nota: first_seen é obrigatório na tabela criada, vamos usar timestamp como first_seen também por enquanto
        query = text("""
            INSERT INTO sentinel_player_wallets 
            (steam_id, player_name, cash, bank, gold, net_worth, total_earned, total_spent, squad_name, last_transaction, first_seen)
            SELECT DISTINCT ON (steam_id)
                steam_id,
                player_name,
                COALESCE(cash, 0) as cash,
                COALESCE(bank, 0) as bank,
                COALESCE(gold, 0) as gold,
                (COALESCE(cash, 0) + COALESCE(bank, 0) + COALESCE(gold, 0)) as net_worth,
                0 as total_earned,
                0 as total_spent,
                NULL as squad_name,
                timestamp as last_transaction,
                timestamp as first_seen
            FROM sentinel_economy_balances
            ORDER BY steam_id, timestamp DESC
        """)
        
        try:
            result = await session.execute(query)
            await session.commit()
            
            # Verificar contagem
            count = (await session.execute(text("SELECT COUNT(*) FROM sentinel_player_wallets"))).scalar()
            print(f"   ✅ {count} jogadores inseridos com sucesso!\n")
            
            # Mostrar Top 5
            print("📊 TOP 5 JOGADORES MAIS RICOS:")
            print("-" * 60)
            top5 = await session.execute(text("""
                SELECT player_name, net_worth, cash, bank, gold 
                FROM sentinel_player_wallets 
                ORDER BY net_worth DESC 
                LIMIT 5
            """))
            
            for i, p in enumerate(top5.fetchall(), 1):
                print(f"#{i} {p[0]:<20} | Net Worth: ${p[1]:,.0f}")
                print(f"    Cash: ${p[2]:,.0f} | Bank: ${p[3]:,.0f} | Gold: {p[4]:,.0f}")
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Erro ao inserir dados: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(upgrade_and_populate())
