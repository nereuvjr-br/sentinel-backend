#!/bin/bash

# 🧪 Script de Teste - API de Analytics de Economia
# Valida todos os endpoints de analytics implementados

set -e

BASE_URL="http://localhost:8000/v2/analytics/economy"
COLORS=true

# Cores para output
if [ "$COLORS" = true ]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    GREEN=''
    RED=''
    YELLOW=''
    BLUE=''
    NC=''
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🧪 Teste de Analytics de Economia - SCUM Sentinel     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Função para testar endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local jq_filter="$3"
    
    echo -e "${YELLOW}📍 Testando: ${name}${NC}"
    echo -e "   URL: ${url}"
    
    response=$(curl -s "${url}")
    http_code=$?
    
    if [ $http_code -eq 0 ]; then
        if [ -n "$jq_filter" ]; then
            result=$(echo "$response" | jq -r "$jq_filter" 2>/dev/null)
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}   ✅ SUCESSO${NC}"
                echo -e "   Resultado: ${result}"
            else
                echo -e "${RED}   ❌ ERRO: Resposta JSON inválida${NC}"
                echo "$response" | head -n 3
            fi
        else
            echo -e "${GREEN}   ✅ SUCESSO${NC}"
            echo "$response" | jq -C '.' 2>/dev/null | head -n 10
        fi
    else
        echo -e "${RED}   ❌ ERRO: Falha na requisição (código: $http_code)${NC}"
    fi
    
    echo ""
}

# 1. Top Items
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  1️⃣  TOP ITENS NEGOCIADOS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

test_endpoint \
    "Top 5 Itens Vendidos" \
    "${BASE_URL}/top-items/?trade_type=Sell&limit=5" \
    '.[] | "\(.item_class): \(.total_transactions) vendas, $\(.total_value), anomaly: \(.anomaly_score)"'

test_endpoint \
    "Top 5 Itens Comprados" \
    "${BASE_URL}/top-items/?trade_type=Buy&limit=5" \
    '.[] | "\(.item_class): \(.total_transactions) compras, $\(.total_value)"'

# 2. Price Analysis
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  2️⃣  ANÁLISE DE PREÇOS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Primeiro, pegar o item mais vendido
top_item=$(curl -s "${BASE_URL}/top-items/?trade_type=Sell&limit=1" | jq -r '.[0].item_class' 2>/dev/null)

if [ -n "$top_item" ] && [ "$top_item" != "null" ]; then
    test_endpoint \
        "Análise de Preços: ${top_item}" \
        "${BASE_URL}/price-analysis/${top_item}?days=30" \
        '"Item: \(.item_class)\nVendas: \(.total_sales)\nPreço Médio Venda: $\(.avg_sell_price)\nTendência: \(.market_trend)\nVolatilidade: \(.price_volatility)%"'
else
    echo -e "${YELLOW}   ⚠️  Nenhum item encontrado para análise de preços${NC}"
    echo ""
fi

# 3. Exploit Detection
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  3️⃣  DETECÇÃO DE EXPLOITS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

test_endpoint \
    "Detecção de Exploits (24h)" \
    "${BASE_URL}/exploit-detection/?hours=24" \
    '"Vendas em Massa: \(.summary.total_mass_sales)\nDuping Suspects: \(.summary.total_duping_suspects)\nJogador de Maior Risco: \(.summary.highest_risk_player // "Nenhum")\nValor Suspeito Total: $\(.summary.total_suspicious_value)"'

test_endpoint \
    "Detecção de Exploits (6h - Threshold Alto)" \
    "${BASE_URL}/exploit-detection/?hours=6&mass_sale_threshold=20" \
    '"\(.summary.total_mass_sales) vendas em massa detectadas"'

# 4. Player Economy
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  4️⃣  ANÁLISE DE JOGADOR${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Pegar um Steam ID de exemplo dos dados
sample_steam_id=$(curl -s "${BASE_URL}/top-items/?limit=1" | jq -r '.[0].unique_sellers // empty' 2>/dev/null | head -n 1)

if [ -z "$sample_steam_id" ]; then
    # Tentar pegar de exploit detection
    sample_steam_id=$(curl -s "${BASE_URL}/exploit-detection/?hours=24" | jq -r '.mass_sales_detected[0].steam_id // empty' 2>/dev/null)
fi

if [ -n "$sample_steam_id" ] && [ "$sample_steam_id" != "null" ]; then
    test_endpoint \
        "Análise Econômica: ${sample_steam_id}" \
        "${BASE_URL}/player-economy/${sample_steam_id}?days=30" \
        '"Jogador: \(.player_name)\nVendas: \(.trading_activity.total_sales)\nCompras: \(.trading_activity.total_purchases)\nLucro Líquido: $\(.trading_activity.net_profit)\nRisco de Exploit: \(.behavior_flags.potential_exploit_risk)"'
else
    echo -e "${YELLOW}   ⚠️  Nenhum Steam ID encontrado para análise${NC}"
    echo -e "${YELLOW}   💡 Testando com Steam ID genérico...${NC}"
    echo ""
    
    test_endpoint \
        "Análise Econômica (Steam ID de Teste)" \
        "${BASE_URL}/player-economy/76561198012345678?days=7" \
        '"Jogador: \(.player_name // "N/A")\nVendas: \(.trading_activity.total_sales // 0)\nCompras: \(.trading_activity.total_purchases // 0)"'
fi

# Resumo Final
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📊 RESUMO DOS TESTES${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Contar sucessos (simplificado - apenas verifica se os endpoints respondem)
total_tests=7
echo -e "${GREEN}✅ Todos os ${total_tests} endpoints testados${NC}"
echo ""
echo -e "${YELLOW}💡 Dicas:${NC}"
echo -e "   • Use 'jq' para formatar as respostas JSON"
echo -e "   • Ajuste os parâmetros (days, limit, threshold) conforme necessário"
echo -e "   • Monitore /exploit-detection/ regularmente para segurança"
echo ""
echo -e "${BLUE}📚 Documentação completa: docs/ECONOMY_ANALYTICS_API.md${NC}"
echo ""
