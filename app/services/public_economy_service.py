from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from app.models.economy_v2 import SentinelEconomyTrade
from app.models.economy_analytics_v2 import SentinelPlayerWallet
from datetime import datetime, timedelta
from app.core.config import settings
import asyncio

class PublicEconomyService:
    _cache = {}
    _cache_ttl = 60  # Reduzido para 1 min, mas desativado na prática

    @classmethod
    async def get_dashboard_summary(cls, session: AsyncSession):
        """
        Retorna o payload completo para o dashboard público de economia.
        Usa dados em tempo real (cache desativado).
        """
        now = datetime.now()
        
        # Cache desativado para garantir realtime
        # cached = cls._cache.get('dashboard_summary')
        # if cached: ...

        try:
            # Executar queries sequencialmente
            server_stats = await cls._get_server_stats(session)
            top_sold = await cls._get_top_items(session, 'Sell', 30)
            top_bought = await cls._get_top_items(session, 'Purchase', 30)
            trends = await cls._get_market_trends(session)

            payload = {
                "server_summary": server_stats,
                "market_trends": trends,
                "top_items_sold": top_sold,
                "top_items_bought": top_bought,
                "meta": {
                    "updated_at": now.strftime("%H:%M:%S"),
                    "next_update_in": 10 # Frontend deve atualizar a cada 10s
                }
            }

            return payload
            
        except Exception as e:
            print(f"Erro ao gerar dashboard público: {e}")
            raise e

    @staticmethod
    async def _get_server_stats(session: AsyncSession):
        """Calcula totais do servidor (usando últimos balances de cada player)"""
        # Buscar da tabela de balances brutos, pegando o último de cada jogador
        query = text("""
            WITH LatestBalances AS (
                SELECT 
                    steam_id, 
                    cash, 
                    bank, 
                    gold,
                    ROW_NUMBER() OVER(PARTITION BY steam_id ORDER BY timestamp DESC) as rn
                FROM sentinel_economy_balances
            )
            SELECT 
                SUM(cash) as total_cash,
                SUM(bank) as total_bank,
                SUM(gold) as total_gold,
                COUNT(*) as active_traders
            FROM LatestBalances
            WHERE rn = 1
        """)
        
        result = await session.execute(query)
        row = result.first()
        
        return {
            "total_cash": {"value": float(row.total_cash or 0), "formatted": f"$ {(row.total_cash or 0):,.0f}".replace(",", ".")},
            "total_bank": {"value": float(row.total_bank or 0), "formatted": f"$ {(row.total_bank or 0):,.0f}".replace(",", ".")},
            "total_gold": {"value": float(row.total_gold or 0), "formatted": f"{(row.total_gold or 0):,.0f} g".replace(",", ".")},
            "total_wealth": {"value": float((row.total_cash or 0) + (row.total_bank or 0)), "formatted": f"$ {((row.total_cash or 0) + (row.total_bank or 0)):,.0f}".replace(",", ".")},
            "active_market_participants": int(row.active_traders or 0)
        }

    @staticmethod
    async def _get_top_items(session: AsyncSession, trade_type: str, limit: int):
        """Busca Top Items em tempo real da tabela de trades"""
        
        # Últimos 7 dias
        cutoff = datetime.now() - timedelta(days=7)
        
        # Query de agregação direta na tabela de logs brutos
        stmt = select(
            SentinelEconomyTrade.item_class,
            func.sum(SentinelEconomyTrade.item_count).label("qty"),
            func.sum(SentinelEconomyTrade.total_price).label("total_value"),
            func.avg(SentinelEconomyTrade.total_price / func.nullif(SentinelEconomyTrade.item_count, 0)).label("avg_price")
        ).where(
            SentinelEconomyTrade.timestamp >= cutoff,
            SentinelEconomyTrade.trade_type == trade_type
        )
        
        # Filtro de itens excluídos via .env
        if settings.excluded_items_list:
            stmt = stmt.where(SentinelEconomyTrade.item_class.not_in(settings.excluded_items_list))
            
        stmt = stmt.group_by(
            SentinelEconomyTrade.item_class
        ).order_by(
            func.sum(SentinelEconomyTrade.total_price).desc()
        ).limit(limit)

        result = await session.execute(stmt)
        rows = result.fetchall()

        return [
            {
                "rank": idx + 1,
                "name": row.item_class,
                "qty": int(row.qty or 0),
                "total_value": f"$ {(row.total_value or 0):,.0f}".replace(",", "."),
                "total_value_raw": float(row.total_value or 0),
                "avg_price": f"$ {(row.avg_price or 0):,.2f}".replace(",", "."),
                "avg_price_raw": float(row.avg_price or 0)
            }
            for idx, row in enumerate(rows)
        ]

    @staticmethod
    async def _get_market_trends(session: AsyncSession):
        """Retorna destaques do mercado (Item mais valioso - Raw Data)"""
        cutoff = datetime.now() - timedelta(days=7)
        
        # Item mais caro (média de venda unitária mais alta)
        stmt = select(
            SentinelEconomyTrade.item_class,
            func.avg(SentinelEconomyTrade.total_price / func.nullif(SentinelEconomyTrade.item_count, 0)).label("avg_price")
        ).where(
            SentinelEconomyTrade.timestamp >= cutoff,
            SentinelEconomyTrade.trade_type == 'Sell' # Apenas vendas para o trader definem valor de mercado? Ou compras? Geralmente Vendas.
        )

        if settings.excluded_items_list:
            stmt = stmt.where(SentinelEconomyTrade.item_class.not_in(settings.excluded_items_list))
            
        stmt = stmt.group_by(SentinelEconomyTrade.item_class)\
            .order_by(func.avg(SentinelEconomyTrade.total_price / func.nullif(SentinelEconomyTrade.item_count, 0)).desc())\
            .limit(1)
            
        result = await session.execute(stmt)
        most_valuable = result.first()
        
        return {
            "most_valuable_item": {
                "name": most_valuable.item_class if most_valuable else "N/A",
                "avg_price": f"$ {(most_valuable.avg_price or 0):,.2f}".replace(",", ".") if most_valuable else "$ 0"
            }
        }
