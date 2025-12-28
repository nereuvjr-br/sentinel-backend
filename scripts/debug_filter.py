
import asyncio
from sqlalchemy import select, func, text
from app.core.database import engine
from app.core.config import settings
from app.models.economy_analytics_v2 import SentinelItemEconomy
from sqlalchemy.ext.asyncio import AsyncSession

async def test_filter():
    print(f"🔧 Config EXCLUDED_ITEMS raw: '{settings.EXCLUDED_ITEMS}'")
    print(f"🔧 Config List: {settings.excluded_items_list}")
    
    async with AsyncSession(engine) as session:
        # 1. Verificar se o item existe no banco sem filtro
        bad_item = "Improvised_Metal_Chest"
        stmt_check = select(func.count()).where(SentinelItemEconomy.item_class == bad_item)
        count = (await session.execute(stmt_check)).scalar()
        print(f"📊 '{bad_item}' no banco (Total): {count} registros")
        
        # 2. Simular a query do Service
        print("\n🔍 Testando Query com Filtro...")
        
        value_col = SentinelItemEconomy.total_sale_value
        
        stmt = select(SentinelItemEconomy.item_class, func.sum(value_col))\
            .where(SentinelItemEconomy.item_class.not_in(settings.excluded_items_list))\
            .group_by(SentinelItemEconomy.item_class)\
            .order_by(func.sum(value_col).desc())\
            .limit(5)
            
        result = await session.execute(stmt)
        rows = result.fetchall()
        
        print("🏆 TOP 5 APÓS FILTRO:")
        for r in rows:
            print(f"   - {r[0]}: ${r[1]:,.0f}")
            if r[0] in settings.excluded_items_list:
                print(f"   ❌ ERRO! O item {r[0]} deveria ter sido filtrado!")

if __name__ == "__main__":
    asyncio.run(test_filter())
