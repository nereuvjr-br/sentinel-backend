-- Migration: Add Economic Analytics Tables
-- Date: 2025-12-26
-- Description: Adiciona 5 tabelas para análise econômica avançada

-- ============================================================================
-- 1. SENTINEL_PLAYER_WALLETS - Consolidação de Carteiras
-- ============================================================================
CREATE TABLE IF NOT EXISTS sentinel_player_wallets (
    steam_id VARCHAR(255) PRIMARY KEY,
    player_name VARCHAR(255) NOT NULL,
    
    -- Saldos Atuais
    cash DOUBLE PRECISION DEFAULT 0,
    bank DOUBLE PRECISION DEFAULT 0,
    gold DOUBLE PRECISION DEFAULT 0,
    
    -- Metadados Financeiros
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

CREATE INDEX idx_wallets_net_worth ON sentinel_player_wallets(net_worth DESC);
CREATE INDEX idx_wallets_last_transaction ON sentinel_player_wallets(last_transaction);

COMMENT ON TABLE sentinel_player_wallets IS 'Consolidação do estado atual da carteira de cada jogador';
COMMENT ON COLUMN sentinel_player_wallets.net_worth IS 'Patrimônio total (cash + bank + gold) - calculado automaticamente';

-- ============================================================================
-- 2. SENTINEL_ITEM_ECONOMY - Análise de Itens
-- ============================================================================
CREATE TABLE IF NOT EXISTS sentinel_item_economy (
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
    avg_sale_health DOUBLE PRECISION,
    avg_sale_uses INTEGER,
    
    -- Análise de Mercado
    price_trend VARCHAR(20),
    demand_level VARCHAR(20),
    
    -- Traders
    most_sold_trader VARCHAR(255),
    most_bought_trader VARCHAR(255),
    
    -- Período de Análise
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(item_class, period_start)
);

CREATE INDEX idx_item_economy_class ON sentinel_item_economy(item_class);
CREATE INDEX idx_item_economy_period ON sentinel_item_economy(period_start, period_end);
CREATE INDEX idx_item_economy_demand ON sentinel_item_economy(demand_level);

COMMENT ON TABLE sentinel_item_economy IS 'Análise agregada da economia de cada item';

-- ============================================================================
-- 3. SENTINEL_ECONOMY_ALERTS - Sistema de Alertas
-- ============================================================================
CREATE TABLE IF NOT EXISTS sentinel_economy_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    
    -- Contexto
    steam_id VARCHAR(255),
    player_name VARCHAR(255),
    trader_name VARCHAR(255),
    item_class VARCHAR(255),
    account_number VARCHAR(50),
    
    -- Detalhes
    description TEXT NOT NULL,
    evidence JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'open',
    assigned_admin VARCHAR(255),
    
    -- Timestamps
    detected_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_type ON sentinel_economy_alerts(alert_type);
CREATE INDEX idx_alerts_severity ON sentinel_economy_alerts(severity);
CREATE INDEX idx_alerts_status ON sentinel_economy_alerts(status);
CREATE INDEX idx_alerts_steam_id ON sentinel_economy_alerts(steam_id);
CREATE INDEX idx_alerts_detected ON sentinel_economy_alerts(detected_at DESC);

COMMENT ON TABLE sentinel_economy_alerts IS 'Sistema de alertas automáticos para anomalias econômicas';

-- ============================================================================
-- 4. SENTINEL_TRADER_INVENTORY - Inventário de Traders
-- ============================================================================
CREATE TABLE IF NOT EXISTS sentinel_trader_inventory (
    id SERIAL PRIMARY KEY,
    trader_name VARCHAR(255) NOT NULL,
    
    -- Estado Financeiro
    funds DOUBLE PRECISION NOT NULL,
    
    -- Estoque
    item_class VARCHAR(255),
    stock_quantity INTEGER,
    
    -- Contexto
    users_online INTEGER,
    
    -- Timestamp
    snapshot_time TIMESTAMP NOT NULL,
    
    UNIQUE(trader_name, item_class, snapshot_time)
);

CREATE INDEX idx_trader_inv_name ON sentinel_trader_inventory(trader_name);
CREATE INDEX idx_trader_inv_time ON sentinel_trader_inventory(snapshot_time DESC);
CREATE INDEX idx_trader_inv_funds ON sentinel_trader_inventory(funds);

COMMENT ON TABLE sentinel_trader_inventory IS 'Rastreamento de estoque e fundos de traders';

-- ============================================================================
-- 5. SENTINEL_ACCOUNT_REGISTRY - Registro de Contas
-- ============================================================================
CREATE TABLE IF NOT EXISTS sentinel_account_registry (
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

CREATE INDEX idx_account_owner ON sentinel_account_registry(current_owner_steam_id);
CREATE INDEX idx_account_active ON sentinel_account_registry(is_active);
CREATE INDEX idx_account_last_tx ON sentinel_account_registry(last_transaction DESC);

COMMENT ON TABLE sentinel_account_registry IS 'Registro de todas as contas bancárias e seus proprietários';
