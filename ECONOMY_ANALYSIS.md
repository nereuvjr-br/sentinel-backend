# Análise e Proposta de Melhorias - Sistema Econômico Sentinel

## 📊 Status Atual do Sistema Econômico

### Tabelas Existentes (5 tabelas)
1. ✅ `sentinel_economy_trades` - Compras e vendas
2. ✅ `sentinel_economy_balances` - Snapshots de saldo
3. ✅ `sentinel_bank_transactions` - Transações bancárias
4. ✅ `sentinel_bank_cards` - Gestão de cartões
5. ✅ `sentinel_mechanic_services` - Serviços de mecânico

---

## 🔍 Dados Atualmente Extraídos

### `sentinel_economy_trades`
**Campos Capturados:**
- ✅ Timestamp, SteamID, Player Name
- ✅ Trade Type (Purchase/Sell)
- ✅ Item Class, Count
- ✅ Item Health, Item Uses (durabilidade)
- ✅ Total Price
- ✅ Trader Name
- ✅ Users Online (contexto de mercado dinâmico)
- ✅ Store Stock Before/After
- ✅ Location (X, Y, Z)

**Dados NÃO Capturados mas Disponíveis:**
- ❌ Account Number do comprador
- ❌ Base Price vs Items Price (em vendas)
- ❌ Saldo do trader (funds)

### `sentinel_economy_balances`
**Campos Capturados:**
- ✅ Timestamp, SteamID, Player Name
- ✅ Trigger Event (Before/After)
- ✅ Trader Name
- ✅ Cash, Bank, Gold (do jogador)
- ✅ Trader Funds

**Problemas Identificados:**
- ❌ Não captura Account Number
- ❌ Não captura Location
- ❌ Dados duplicados (Before/After na mesma transação)

### `sentinel_bank_transactions`
**Campos Capturados:**
- ✅ Timestamp, SteamID, Player Name, Account Number
- ✅ Transaction Type (deposit/withdraw/transfer)
- ✅ Gross Amount, Net Amount, Fee
- ✅ Target Account, Target Name, Target SteamID
- ✅ Location

**Oportunidades:**
- ⚠️ Não rastreia saldo antes/depois
- ⚠️ Não vincula com economy_balances

---

## 🎯 PROPOSTAS DE NOVAS TABELAS

### 1. **`sentinel_player_wallets`** ⭐⭐⭐⭐⭐ (PRIORIDADE MÁXIMA)

**Objetivo:** Consolidar estado atual da carteira de cada jogador

**Justificativa:**
- Atualmente só temos snapshots esparsos em `economy_balances`
- Impossível saber saldo atual de um jogador sem processar todo histórico
- Necessário para dashboards em tempo real
- Base para detecção de exploits econômicos

**Estrutura:**
```sql
CREATE TABLE sentinel_player_wallets (
    steam_id VARCHAR(255) PRIMARY KEY,
    player_name VARCHAR(255) NOT NULL,
    
    -- Saldos Atuais
    cash DOUBLE PRECISION DEFAULT 0,
    bank DOUBLE PRECISION DEFAULT 0,
    gold DOUBLE PRECISION DEFAULT 0,
    
    -- Metadados
    total_earned DOUBLE PRECISION DEFAULT 0,
    total_spent DOUBLE PRECISION DEFAULT 0,
    net_worth DOUBLE PRECISION GENERATED ALWAYS AS (cash + bank + gold) STORED,
    
    -- Contas Bancárias
    primary_account_number VARCHAR(50),
    account_count INTEGER DEFAULT 0,
    
    -- Timestamps
    first_seen TIMESTAMP NOT NULL,
    last_transaction TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Atualização:** Trigger ou processo batch que atualiza após cada transação

**Benefícios:**
- ✅ Ranking de jogadores mais ricos
- ✅ Detecção de inflação/deflação
- ✅ Identificação de dupers (saldo anormal)
- ✅ Dashboard de economia em tempo real

---

### 2. **`sentinel_trader_inventory`** ⭐⭐⭐⭐ (ALTA PRIORIDADE)

**Objetivo:** Rastrear estoque e fundos de cada trader

**Justificativa:**
- Traders podem ficar "quebrados" (sem fundos)
- Estoque de itens importantes pode esgotar
- Necessário para balanceamento econômico
- Detectar exploits de farming de traders

**Estrutura:**
```sql
CREATE TABLE sentinel_trader_inventory (
    id SERIAL PRIMARY KEY,
    trader_name VARCHAR(255) NOT NULL,
    
    -- Estado Financeiro
    funds DOUBLE PRECISION NOT NULL,
    
    -- Estoque (agregado por item)
    item_class VARCHAR(255),
    stock_quantity INTEGER,
    
    -- Contexto
    users_online INTEGER,
    
    -- Timestamps
    snapshot_time TIMESTAMP NOT NULL,
    
    UNIQUE(trader_name, item_class, snapshot_time)
);
```

**Atualização:** Snapshot a cada transação (ou agregado por hora)

**Benefícios:**
- ✅ Alertas quando trader fica sem fundos
- ✅ Monitorar itens em falta
- ✅ Análise de demanda por item
- ✅ Balanceamento de preços

---

### 3. **`sentinel_item_economy`** ⭐⭐⭐⭐⭐ (PRIORIDADE MÁXIMA)

**Objetivo:** Análise detalhada da economia de cada item

**Justificativa:**
- Identificar itens mais valiosos
- Detectar manipulação de mercado
- Análise de durabilidade (health/uses)
- Base para ajuste de preços

**Estrutura:**
```sql
CREATE TABLE sentinel_item_economy (
    id SERIAL PRIMARY KEY,
    item_class VARCHAR(255) NOT NULL,
    
    -- Estatísticas de Compra
    total_purchases BIGINT DEFAULT 0,
    total_purchase_value DOUBLE PRECISION DEFAULT 0,
    avg_purchase_price DOUBLE PRECISION,
    
    -- Estatísticas de Venda
    total_sales BIGINT DEFAULT 0,
    total_sale_value DOUBLE PRECISION DEFAULT 0,
    avg_sale_price DOUBLE PRECISION,
    avg_sale_health DOUBLE PRECISION,  -- Durabilidade média em vendas
    avg_sale_uses INTEGER,             -- Munição/cargas médias
    
    -- Análise de Mercado
    price_trend VARCHAR(20),  -- rising, falling, stable
    demand_level VARCHAR(20), -- high, medium, low
    
    -- Traders
    most_sold_trader VARCHAR(255),
    most_bought_trader VARCHAR(255),
    
    -- Período de Análise
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(item_class, period_start)
);
```

**Atualização:** Agregação diária/semanal

**Benefícios:**
- ✅ Dashboard de itens mais negociados
- ✅ Detectar itens "quebrados" sendo vendidos
- ✅ Análise de inflação por item
- ✅ Recomendações de balanceamento

---

### 4. **`sentinel_account_registry`** ⭐⭐⭐ (MÉDIA PRIORIDADE)

**Objetivo:** Registro de todas as contas bancárias

**Justificativa:**
- Jogadores podem ter múltiplas contas
- Rastrear transferências suspeitas entre contas
- Detectar lavagem de dinheiro
- Histórico de ownership de contas

**Estrutura:**
```sql
CREATE TABLE sentinel_account_registry (
    account_number VARCHAR(50) PRIMARY KEY,
    
    -- Proprietário Atual
    current_owner_steam_id VARCHAR(255) NOT NULL,
    current_owner_name VARCHAR(255) NOT NULL,
    
    -- Histórico
    created_at TIMESTAMP NOT NULL,
    last_transaction TIMESTAMP,
    
    -- Estatísticas
    total_deposits DOUBLE PRECISION DEFAULT 0,
    total_withdrawals DOUBLE PRECISION DEFAULT 0,
    total_transfers_in DOUBLE PRECISION DEFAULT 0,
    total_transfers_out DOUBLE PRECISION DEFAULT 0,
    
    -- Flags
    is_active BOOLEAN DEFAULT TRUE,
    has_card BOOLEAN DEFAULT FALSE,
    card_type VARCHAR(100),
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Benefícios:**
- ✅ Rastrear múltiplas contas por jogador
- ✅ Detectar transferências circulares (lavagem)
- ✅ Histórico de ownership
- ✅ Análise de uso de cartões

---

### 5. **`sentinel_economy_alerts`** ⭐⭐⭐⭐ (ALTA PRIORIDADE)

**Objetivo:** Sistema de alertas automáticos para anomalias econômicas

**Justificativa:**
- Detecção proativa de exploits
- Alertas de inflação/deflação
- Notificação de transações suspeitas
- Monitoramento de traders

**Estrutura:**
```sql
CREATE TABLE sentinel_economy_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,  -- dupe_detected, inflation_spike, trader_broke, suspicious_transfer
    severity VARCHAR(20) NOT NULL,     -- low, medium, high, critical
    
    -- Contexto
    steam_id VARCHAR(255),
    player_name VARCHAR(255),
    trader_name VARCHAR(255),
    item_class VARCHAR(255),
    account_number VARCHAR(50),
    
    -- Detalhes
    description TEXT NOT NULL,
    evidence JSONB,  -- Dados que geraram o alerta
    
    -- Status
    status VARCHAR(20) DEFAULT 'open',  -- open, investigating, resolved, false_positive
    assigned_admin VARCHAR(255),
    
    -- Timestamps
    detected_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tipos de Alertas:**
1. **Dupe Detection:** Saldo aumentou drasticamente sem transações
2. **Inflation Spike:** Preço médio de item subiu >50% em 24h
3. **Trader Broke:** Trader ficou sem fundos
4. **Suspicious Transfer:** Transferência circular entre contas
5. **Item Flood:** Jogador vendeu >100 unidades do mesmo item
6. **Negative Balance:** Saldo negativo detectado

**Benefícios:**
- ✅ Detecção automática de exploits
- ✅ Priorização de investigações
- ✅ Histórico de incidentes
- ✅ Métricas de segurança econômica

---

## 📈 MELHORIAS NOS PARSERS EXISTENTES

### `EconomyParserV2` - Enhancements

#### 1. Capturar Account Number em Trades
**Problema:** Trades não salvam account_number  
**Solução:** Adicionar campo `account_number` em `SentinelEconomyTrade`

#### 2. Capturar Location em Balances
**Problema:** Balances não têm coordenadas  
**Solução:** Extrair location do contexto (se disponível)

#### 3. Separar Base Price em Sells
**Problema:** Não diferenciamos preço base vs. valor de itens contidos  
**Solução:** Adicionar campos `base_price` e `contained_items_value`

---

## 🚀 PLANO DE IMPLEMENTAÇÃO

### Fase 1: Consolidação (AGORA)
1. ✅ Criar `sentinel_player_wallets`
2. ✅ Criar `sentinel_item_economy`
3. ✅ Criar `sentinel_economy_alerts`

### Fase 2: Análise Avançada (PRÓXIMA)
4. ✅ Criar `sentinel_trader_inventory`
5. ✅ Criar `sentinel_account_registry`

### Fase 3: Automação (FUTURO)
6. ✅ Triggers para atualizar wallets
7. ✅ Jobs agendados para agregações
8. ✅ Sistema de alertas automáticos

---

## 💡 CASOS DE USO PRÁTICOS

### Dashboard de Economia
- Top 10 jogadores mais ricos
- Gráfico de inflação (últimos 7 dias)
- Itens mais negociados (hoje)
- Traders com baixo estoque
- Alertas econômicos ativos

### Investigação de Exploits
1. Jogador reportado por "dupe"
2. Consultar `sentinel_player_wallets` → Saldo atual
3. Consultar `sentinel_economy_alerts` → Alertas relacionados
4. Consultar `sentinel_bank_transactions` → Transferências suspeitas
5. Consultar `sentinel_economy_trades` → Vendas anormais

### Balanceamento
1. Consultar `sentinel_item_economy` → Itens mais caros
2. Analisar `avg_sale_health` → Itens vendidos quebrados
3. Consultar `sentinel_trader_inventory` → Estoque de traders
4. Ajustar preços/spawn rates

---

## 📊 RESUMO EXECUTIVO

**Tabelas Propostas:** 5 novas tabelas  
**Prioridade Máxima:** 3 tabelas (Wallets, Item Economy, Alerts)  
**Impacto Esperado:**  
- ✅ Detecção automática de exploits econômicos
- ✅ Dashboard de economia em tempo real
- ✅ Análise profunda de mercado
- ✅ Balanceamento baseado em dados
- ✅ Redução de 80% no tempo de investigação

**Próximo Passo:** Implementar as 3 tabelas de prioridade máxima
