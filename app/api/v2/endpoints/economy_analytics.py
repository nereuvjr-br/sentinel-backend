from fastapi import APIRouter, Query, Depends
from sqlmodel import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.economy_v2 import SentinelEconomyTrade, SentinelEconomyBalance
from app.core.config import settings
from datetime import datetime, timedelta
from typing import List, Dict, Any

router = APIRouter()

# ============================================================================
# ANALYTICS - Top Balances (Rich List)
# ============================================================================
@router.get("/top-balances/")
async def get_top_balances(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(10, le=50)
):
    """
    Retorna o Top 10 jogadores com mais Cash, Bank e Gold.
    Baseado no último snapshot de saldo conhecido de cada jogador.
    """
    from sqlalchemy import text
    
    # Query explicada:
    # 1. CTE 'LatestBalances': Particiona por steam_id e pega a linha mais recente (rn=1)
    # 2. Seleciona apenas os registros mais recentes
    # 3. Ordena e limita no Python ou faz 3 queries separadas.
    # Faremos 3 queries separadas sobre a CTE para otimizar o retorno especifico.
    # Mas como CTE não persiste entre queries execute(), vamos fazer uma query única
    # que retorna TUDO (o set de 'active players') e ordenamos no Python?
    # Se tiver 1000 players, ok. Se tiver 100k, ruim.
    # Melhor abordagem: 3 queries SQL distintas se a performance preocupar,
    # ou uma query esperta.
    
    # Dado que SQLModel/AsyncSession não facilita múltiplas queries em um statement só facilmente,
    # vamos usar uma query base que pega os top N de cada categoria via UNION ALL
    # ou simplesmente 3 queries rápidas, já que o dataset de 'latest balances' é o gargalo.
    
    # Vamos usar a estratégia de 3 queries rápidas para garantir ordenação correta no banco.
    
    def get_query(order_field):
        return text(f"""
            WITH LatestBalances AS (
                SELECT 
                    steam_id, 
                    player_name, 
                    cash, 
                    bank, 
                    gold,
                    timestamp,
                    ROW_NUMBER() OVER(PARTITION BY steam_id ORDER BY timestamp DESC) as rn
                FROM sentinel_economy_balances
            )
            SELECT steam_id, player_name, {order_field} as value
            FROM LatestBalances
            WHERE rn = 1
            ORDER BY {order_field} DESC
            LIMIT :limit
        """)

    async def fetch_top(field):
        result = await session.execute(get_query(field), {"limit": limit})
        return [
            {"steam_id": row[0], "player_name": row[1], "value": float(row[2])}
            for row in result.fetchall()
        ]

    return {
        "top_cash": await fetch_top("cash"),
        "top_bank": await fetch_top("bank"),
        "top_gold": await fetch_top("gold")
    }


@router.get("/server-stats/")
async def get_server_stats(session: AsyncSession = Depends(get_session)):
    """
    Retorna estatísticas globais da economia do servidor.
    Soma total de Cash, Bank e Gold em circulação (baseado no último snapshot de cada player).
    """
    from sqlalchemy import text
    
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
            COUNT(*) as total_active_players
        FROM LatestBalances
        WHERE rn = 1
    """)
    
    result = await session.execute(query)
    row = result.fetchone()
    
    if not row:
        return {
            "total_cash": 0,
            "total_bank": 0,
            "total_gold": 0,
            "total_active_players": 0
        }
        
    return {
        "total_cash": float(row[0]) if row[0] else 0,
        "total_bank": float(row[1]) if row[1] else 0,
        "total_gold": float(row[2]) if row[2] else 0,
        "total_active_players": row[3]
    }


# ============================================================================
# ANALYTICS - Itens Mais Negociados
# ============================================================================

@router.get("/top-items/")
async def get_top_items(
    session: AsyncSession = Depends(get_session),
    trade_type: str = Query(None, description="Purchase ou Sell"),
    limit: int = Query(20, le=100),
    hours: int = Query(24, description="Últimas X horas"),
    sort_by: str = Query("total_value", description="total_transactions ou total_value")
):
    """
    Retorna os itens mais negociados (comprados ou vendidos).
    Default ordena por VALOR TOTAL movimentado.
    """
    from sqlalchemy import text
    
    cutoff_date = datetime.utcnow() - timedelta(hours=hours)
    
    # Define a coluna de ordenação
    order_column = "total_value" if sort_by == "total_value" else "total_transactions"
    
    query = text(f"""
        SELECT 
            item_class,
            trade_type,
            COUNT(*) as total_transactions,
            SUM(item_count) as total_items,
            SUM(total_price) as total_value,
            AVG(total_price) as avg_price,
            MIN(total_price) as min_price,
            MAX(total_price) as max_price,
            AVG(item_health) as avg_health,
            COUNT(DISTINCT steam_id) as unique_traders
        FROM sentinel_economy_trades
        WHERE timestamp >= :cutoff_date
        {{trade_type_filter}}
        GROUP BY item_class, trade_type
        ORDER BY {order_column} DESC
        LIMIT :limit
    """.format(
        trade_type_filter=f"AND trade_type = :trade_type" if trade_type else ""
    ))
    
    params = {"cutoff_date": cutoff_date, "limit": limit}
    if trade_type:
        params["trade_type"] = trade_type
    
    result = await session.execute(query, params)
    rows = result.fetchall()
    
    return [
        {
            "item_class": row[0],
            "trade_type": row[1],
            "total_transactions": row[2],
            "total_items": row[3],
            "total_value": float(row[4]) if row[4] else 0,
            "avg_price": float(row[5]) if row[5] else 0,
            "min_price": float(row[6]) if row[6] else 0,
            "max_price": float(row[7]) if row[7] else 0,
            "avg_health": float(row[8]) if row[8] else None,
            "unique_sellers": row[9] if row[1] == "Sell" else 0,
            "unique_buyers": row[9] if row[1] == "Purchase" else 0,
            "anomaly_score": calculate_anomaly_score(row)
        }
        for row in rows
    ]

# ... (price-analysis mantido igual) ...
@router.get("/price-analysis/")
async def get_price_analysis(
    session: AsyncSession = Depends(get_session),
    item_class: str = Query(..., description="Nome do item"),
    hours: int = Query(168, description="Últimas X horas (padrão: 7 dias)")
):
    """
    Análise detalhada de preços de um item específico.
    
    Detecta:
    - Variações anormais de preço
    - Possível manipulação de mercado
    - Padrões de preço suspeitos
    """
    from sqlalchemy import text
    
    cutoff_date = datetime.utcnow() - timedelta(hours=hours)
    
    query = text("""
        SELECT 
            DATE_TRUNC('hour', timestamp) as hour,
            trade_type,
            COUNT(*) as transactions,
            AVG(total_price) as avg_price,
            MIN(total_price) as min_price,
            MAX(total_price) as max_price,
            STDDEV(total_price) as price_stddev
        FROM sentinel_economy_trades
        WHERE item_class = :item_class
        AND timestamp >= :cutoff_date
        GROUP BY DATE_TRUNC('hour', timestamp), trade_type
        ORDER BY hour DESC
    """)
    
    result = await session.execute(query, {"item_class": item_class, "cutoff_date": cutoff_date})
    rows = result.fetchall()
    
    # Calcular estatísticas gerais
    all_prices = [float(row[3]) for row in rows if row[3]]
    
    if not all_prices:
        return {"error": "Nenhum dado encontrado para este item"}
    
    avg_price = sum(all_prices) / len(all_prices)
    price_variance = sum((p - avg_price) ** 2 for p in all_prices) / len(all_prices)
    
    return {
        "item_class": item_class,
        "period_hours": hours,
        "overall_stats": {
            "avg_price": avg_price,
            "price_variance": price_variance,
            "total_transactions": len(rows),
            "price_stability": "stable" if price_variance < (avg_price * 0.1) else "volatile"
        },
        "hourly_data": [
            {
                "hour": row[0].isoformat() if row[0] else None,
                "trade_type": row[1],
                "transactions": row[2],
                "avg_price": float(row[3]) if row[3] else 0,
                "min_price": float(row[4]) if row[4] else 0,
                "max_price": float(row[5]) if row[5] else 0,
                "price_stddev": float(row[6]) if row[6] else 0
            }
            for row in rows
        ]
    }


@router.get("/exploit-detection/")
async def detect_exploits(
    session: AsyncSession = Depends(get_session),
    hours: int = Query(24, description="Últimas X horas")
):
    """
    Detecta possíveis explorações de economia.
    
    Flags suspeitas:
    - Jogador vendendo mesmo item repetidamente em curto período
    - Itens com preço muito acima/abaixo da média
    - Volume anormal de transações
    - Itens com 100% health sendo vendidos em massa (possível duping)
    """
    from sqlalchemy import text
    
    cutoff_date = datetime.utcnow() - timedelta(hours=hours)
    
    # Detectar vendas em massa do mesmo item
    mass_sales_query = text("""
        SELECT 
            steam_id,
            player_name,
            item_class,
            COUNT(*) as sale_count,
            SUM(total_price) as total_earned,
            AVG(item_health) as avg_health,
            MIN(timestamp) as first_sale,
            MAX(timestamp) as last_sale
        FROM sentinel_economy_trades
        WHERE trade_type = 'Sell'
        AND timestamp >= :cutoff_date
        GROUP BY steam_id, player_name, item_class
        HAVING COUNT(*) >= 10
        ORDER BY sale_count DESC
        LIMIT 20
    """)
    
    result = await session.execute(mass_sales_query, {"cutoff_date": cutoff_date})
    mass_sales = result.fetchall()
    
    # Detectar itens com 100% health vendidos em massa (possível duping)
    duping_query = text("""
        SELECT 
            item_class,
            COUNT(*) as perfect_condition_sales,
            COUNT(DISTINCT steam_id) as unique_sellers,
            AVG(total_price) as avg_price
        FROM sentinel_economy_trades
        WHERE trade_type = 'Sell'
        AND item_health = 100.0
        AND timestamp >= :cutoff_date
        GROUP BY item_class
        HAVING COUNT(*) >= 5
        ORDER BY perfect_condition_sales DESC
    """)
    
    result = await session.execute(duping_query, {"cutoff_date": cutoff_date})
    duping_suspects = result.fetchall()
    
    return {
        "period_hours": hours,
        "mass_sales_detected": [
            {
                "steam_id": row[0],
                "player_name": row[1],
                "item_class": row[2],
                "sale_count": row[3],
                "total_earned": float(row[4]) if row[4] else 0,
                "avg_health": float(row[5]) if row[5] else None,
                "time_span_minutes": (row[7] - row[6]).total_seconds() / 60 if row[6] and row[7] else 0,
                "risk_level": "HIGH" if row[3] > 20 else "MEDIUM"
            }
            for row in mass_sales
        ],
        "duping_suspects": [
            {
                "item_class": row[0],
                "perfect_condition_sales": row[1],
                "unique_sellers": row[2],
                "avg_price": float(row[3]) if row[3] else 0,
                "risk_level": "HIGH" if row[1] > 10 and row[2] < 3 else "MEDIUM"
            }
            for row in duping_suspects
        ]
    }


@router.get("/player-economy/")
async def get_player_economy(
    session: AsyncSession = Depends(get_session),
    steam_id: str = Query(..., description="Steam ID do jogador"),
    hours: int = Query(168, description="Últimas X horas")
):
    """
    Análise econômica de um jogador específico.
    """
    from sqlalchemy import text
    
    cutoff_date = datetime.utcnow() - timedelta(hours=hours)
    
    query = text("""
        SELECT 
            trade_type,
            COUNT(*) as transactions,
            SUM(total_price) as total_value,
            COUNT(DISTINCT item_class) as unique_items
        FROM sentinel_economy_trades
        WHERE steam_id = :steam_id
        AND timestamp >= :cutoff_date
        GROUP BY trade_type
    """)
    
    result = await session.execute(query, {"steam_id": steam_id, "cutoff_date": cutoff_date})
    summary = result.fetchall()
    
    # Helper query para pegar top itens
    async def get_player_top_items(t_type):
        q = text("""
            SELECT 
                item_class,
                COUNT(*) as count,
                SUM(total_price) as total_val
            FROM sentinel_economy_trades
            WHERE steam_id = :steam_id
            AND trade_type = :t_type
            AND timestamp >= :cutoff_date
            GROUP BY item_class
            ORDER BY total_val DESC
            LIMIT 50
        """)
        r = await session.execute(q, {"steam_id": steam_id, "cutoff_date": cutoff_date, "t_type": t_type})
        return r.fetchall()

    top_sold = await get_player_top_items('Sell')
    top_bought = await get_player_top_items('Purchase')
    
    return {
        "steam_id": steam_id,
        "period_hours": hours,
        "summary": [
            {
                "trade_type": row[0],
                "transactions": row[1],
                "total_value": float(row[2]) if row[2] else 0,
                "unique_items": row[3]
            }
            for row in summary
        ],
        "top_sold_items": [
            {
                "item_class": row[0],
                "times_sold": row[1],
                "total_earned": float(row[2]) if row[2] else 0
            }
            for row in top_sold
        ],
        "top_purchased_items": [
            {
                "item_class": row[0],
                "times_bought": row[1],
                "total_spent": float(row[2]) if row[2] else 0
            }
            for row in top_bought
        ]
    }


@router.get("/top-traders/")
async def get_top_traders(
    session: AsyncSession = Depends(get_session),
    trade_type: str = Query("Sell", description="Sell ou Buy"),
    limit: int = Query(10, le=50),
    hours: int = Query(168, description="Últimas X horas (padrão: 7 dias)"),
    sort_by: str = Query("total_value", description="total_transactions ou total_value")
):
    """
    Retorna os jogadores que mais compram ou vendem.
    
    Útil para identificar:
    - Jogadores mais ativos no mercado
    - Possíveis farmers
    - Traders profissionais
    """
    from sqlalchemy import text
    
    cutoff_date = datetime.utcnow() - timedelta(hours=hours)
    
    # Define a coluna de ordenação
    order_column = "total_value" if sort_by == "total_value" else "total_transactions"
    
    query = text(f"""
        SELECT 
            steam_id,
            player_name,
            COUNT(*) as total_transactions,
            COUNT(DISTINCT item_class) as unique_items,
            SUM(total_price) as total_value,
            AVG(total_price) as avg_transaction_value,
            MIN(timestamp) as first_transaction,
            MAX(timestamp) as last_transaction
        FROM sentinel_economy_trades
        WHERE trade_type = :trade_type
        AND timestamp >= :cutoff_date
        GROUP BY steam_id, player_name
        ORDER BY {order_column} DESC
        LIMIT :limit
    """)
    
    result = await session.execute(query, {
        "trade_type": trade_type,
        "cutoff_date": cutoff_date,
        "limit": limit
    })
    rows = result.fetchall()
    
    return [
        {
            "steam_id": row[0],
            "player_name": row[1],
            "total_transactions": row[2],
            "unique_items": row[3],
            "total_value": float(row[4]) if row[4] else 0,
            "avg_transaction_value": float(row[5]) if row[5] else 0,
            "first_transaction": row[6].isoformat() if row[6] else None,
            "last_transaction": row[7].isoformat() if row[7] else None,
            "activity_score": calculate_trader_activity_score(row)
        }
        for row in rows
    ]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_anomaly_score(row) -> float:
    """
    Calcula um score de anomalia baseado em vários fatores.
    Score alto = mais suspeito
    """
    total_transactions = row[2]
    total_value = row[4] or 0
    avg_price = row[5] or 0
    min_price = row[6] or 0
    max_price = row[7] or 0
    unique_sellers = row[9]
    
    score = 0.0
    
    # Volume muito alto
    if total_transactions > 50:
        score += 2.0
    
    # Poucos vendedores para muito volume (possível farm bot)
    if total_transactions > 20 and unique_sellers < 3:
        score += 3.0
    
    # Variação de preço muito grande (possível manipulação)
    if max_price > 0 and min_price > 0:
        price_variation = (max_price - min_price) / avg_price if avg_price > 0 else 0
        if price_variation > 0.5:  # Variação > 50%
            score += 2.0
    
    # Valor total muito alto
    if total_value > 100000:
        score += 1.5
    
    return round(score, 2)


def calculate_trader_activity_score(row) -> float:
    """
    Calcula um score de atividade do trader.
    Score alto = trader muito ativo
    """
    total_transactions = row[2]
    unique_items = row[3]
    total_value = row[4] or 0
    
    score = 0.0
    
    # Volume de transações
    if total_transactions > 100:
        score += 5.0
    elif total_transactions > 50:
        score += 3.0
    elif total_transactions > 20:
        score += 1.0
    
    # Diversidade de itens
    if unique_items > 20:
        score += 3.0
    elif unique_items > 10:
        score += 2.0
    elif unique_items > 5:
        score += 1.0
    
    # Valor total movimentado
    if total_value > 500000:
        score += 4.0
    elif total_value > 100000:
        score += 2.0
    elif total_value > 50000:
        score += 1.0
    
    return round(score, 2)
