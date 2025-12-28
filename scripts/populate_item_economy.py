"""
Script para popular sentinel_item_economy a partir de sentinel_economy_trades
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

async def populate_item_economy():
    print("🔄 Populando sentinel_item_economy...\n")
    
    async with AsyncSession(engine) as session:
        # 1. Verificar se existem logs na tabela de trades
        tables_res = await session.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
        tables = [r[0] for r in tables_res.fetchall()]
        
        trade_table = None
        if 'sentinel_economy_trades' in tables:
            trade_table = 'sentinel_economy_trades'
        elif 'sentinel_economy_trade' in tables:
            trade_table = 'sentinel_economy_trade'
        elif 'sentinel_trades' in tables:
            trade_table = 'sentinel_trades'
            
        if not trade_table:
            print("❌ Nenhuma tabela de logs de trade encontrada.")
            return

        print(f"   📂 Usando tabela de fonte: {trade_table}")

        # 2. Limpar item economy
        await session.execute(text("TRUNCATE TABLE sentinel_item_economy"))
        await session.commit()
        print("   ✅ Tabela sentinel_item_economy limpa")

        # Configurar nomes de colunas
        col_item = 'item_class'
        col_type = 'trade_type' 
        col_price = 'total_price'
        col_qty = 'item_count'
        
        print(f"      Mapeando: Item={col_item}, Type={col_type}, Price={col_price}, Qty={col_qty}")

        # 3. Inserir dados agregados
        # DEFININDO DATAS RECENTES (NOW) para garantir que apareça nos dashboards de "7 dias"
        query = text(f"""
            INSERT INTO sentinel_item_economy 
            (item_class, total_purchases, total_purchase_value, avg_purchase_price, 
             total_sales, total_sale_value, avg_sale_price, period_start, period_end)
            SELECT
                {col_item},
                SUM(CASE WHEN {col_type} = 'Purchase' THEN {col_qty} ELSE 0 END) as buys,
                SUM(CASE WHEN {col_type} = 'Purchase' THEN value_total ELSE 0 END) as buy_val,
                CASE WHEN SUM(CASE WHEN {col_type} = 'Purchase' THEN {col_qty} ELSE 0 END) > 0 
                     THEN SUM(CASE WHEN {col_type} = 'Purchase' THEN value_total ELSE 0 END) / SUM(CASE WHEN {col_type} = 'Purchase' THEN {col_qty} ELSE 0 END)
                     ELSE 0 END as avg_buy,
                     
                SUM(CASE WHEN {col_type} = 'Sell' THEN {col_qty} ELSE 0 END) as sells,
                SUM(CASE WHEN {col_type} = 'Sell' THEN value_total ELSE 0 END) as sell_val,
                CASE WHEN SUM(CASE WHEN {col_type} = 'Sell' THEN {col_qty} ELSE 0 END) > 0 
                     THEN SUM(CASE WHEN {col_type} = 'Sell' THEN value_total ELSE 0 END) / SUM(CASE WHEN {col_type} = 'Sell' THEN {col_qty} ELSE 0 END)
                     ELSE 0 END as avg_sell,
                NOW(),
                NOW()
            FROM (SELECT *, {col_price} as value_total FROM {trade_table}) as sub
            GROUP BY {col_item}
        """)

        try:
            await session.execute(query)
            await session.commit()
            
            count = (await session.execute(text("SELECT COUNT(*) FROM sentinel_item_economy"))).scalar()
            print(f"   ✅ {count} registros de itens inseridos!\n")
            
            # Mostrar Top 3
            print("📊 TOP 3 ITEMS VENDIDOS:")
            top3 = await session.execute(text("""
                SELECT item_class, total_sales, total_sale_value 
                FROM sentinel_item_economy 
                ORDER BY total_sale_value DESC LIMIT 3
            """))
            for r in top3:
                print(f"   - {r[0]}: {r[1]} unids (${r[2]:,.0f})")

        except Exception as e:
            print(f"❌ Erro na agregação SQL: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(populate_item_economy())
