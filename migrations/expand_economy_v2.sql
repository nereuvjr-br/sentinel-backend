"""
Migration: Expand Economy Models V2
Adds new tables for comprehensive economy tracking:
- sentinel_bank_transactions
- sentinel_mechanic_services  
- sentinel_bank_cards
- sentinel_unparsed_logs

Also adds new columns to existing economy tables.
"""

-- ============================================================================
-- 1. ALTER EXISTING TABLES - Add new columns
-- ============================================================================

-- Add columns to sentinel_economy_trades
ALTER TABLE sentinel_economy_trades 
ADD COLUMN IF NOT EXISTS account_number VARCHAR,
ADD COLUMN IF NOT EXISTS item_health FLOAT,
ADD COLUMN IF NOT EXISTS item_uses INTEGER,
ADD COLUMN IF NOT EXISTS is_mechanic_service BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS pos_x FLOAT,
ADD COLUMN IF NOT EXISTS pos_y FLOAT,
ADD COLUMN IF NOT EXISTS pos_z FLOAT;

-- Add columns to sentinel_economy_balances
ALTER TABLE sentinel_economy_balances
ADD COLUMN IF NOT EXISTS account_number VARCHAR,
ADD COLUMN IF NOT EXISTS pos_x FLOAT,
ADD COLUMN IF NOT EXISTS pos_y FLOAT,
ADD COLUMN IF NOT EXISTS pos_z FLOAT;

-- ============================================================================
-- 2. CREATE NEW TABLES
-- ============================================================================

-- Bank Transactions (Deposits, Withdrawals, Transfers)
CREATE TABLE IF NOT EXISTS sentinel_bank_transactions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    steam_id VARCHAR NOT NULL,
    player_name VARCHAR NOT NULL,
    account_number VARCHAR NOT NULL,
    transaction_type VARCHAR NOT NULL,  -- 'deposit', 'withdraw', 'transfer'
    gross_amount FLOAT NOT NULL,
    net_amount FLOAT NOT NULL,
    fee FLOAT,
    target_account VARCHAR,
    target_name VARCHAR,
    target_steam_id VARCHAR,
    pos_x FLOAT NOT NULL,
    pos_y FLOAT NOT NULL,
    pos_z FLOAT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bank_trans_timestamp ON sentinel_bank_transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_bank_trans_steam_id ON sentinel_bank_transactions(steam_id);
CREATE INDEX IF NOT EXISTS idx_bank_trans_account ON sentinel_bank_transactions(account_number);
CREATE INDEX IF NOT EXISTS idx_bank_trans_type ON sentinel_bank_transactions(transaction_type);

-- Mechanic Services
CREATE TABLE IF NOT EXISTS sentinel_mechanic_services (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    steam_id VARCHAR NOT NULL,
    player_name VARCHAR NOT NULL,
    service_type VARCHAR NOT NULL,  -- 'Buy', 'Install', 'Repair', 'Remove'
    item_class VARCHAR NOT NULL,
    price FLOAT NOT NULL,
    trader_name VARCHAR NOT NULL,
    pos_x FLOAT,
    pos_y FLOAT,
    pos_z FLOAT
);

CREATE INDEX IF NOT EXISTS idx_mechanic_timestamp ON sentinel_mechanic_services(timestamp);
CREATE INDEX IF NOT EXISTS idx_mechanic_steam_id ON sentinel_mechanic_services(steam_id);
CREATE INDEX IF NOT EXISTS idx_mechanic_service_type ON sentinel_mechanic_services(service_type);
CREATE INDEX IF NOT EXISTS idx_mechanic_item ON sentinel_mechanic_services(item_class);

-- Bank Card Management
CREATE TABLE IF NOT EXISTS sentinel_bank_cards (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    steam_id VARCHAR NOT NULL,
    player_name VARCHAR NOT NULL,
    account_number VARCHAR NOT NULL,
    action VARCHAR NOT NULL,  -- 'purchased', 'manually destroyed'
    card_type VARCHAR NOT NULL,  -- 'Starter card', 'Gold card', 'Classic card'
    free_renewal BOOLEAN,
    new_balance FLOAT,
    destroyed_account VARCHAR,
    pos_x FLOAT NOT NULL,
    pos_y FLOAT NOT NULL,
    pos_z FLOAT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bank_card_timestamp ON sentinel_bank_cards(timestamp);
CREATE INDEX IF NOT EXISTS idx_bank_card_steam_id ON sentinel_bank_cards(steam_id);
CREATE INDEX IF NOT EXISTS idx_bank_card_account ON sentinel_bank_cards(account_number);
CREATE INDEX IF NOT EXISTS idx_bank_card_action ON sentinel_bank_cards(action);
CREATE INDEX IF NOT EXISTS idx_bank_card_type ON sentinel_bank_cards(card_type);

-- Unparsed Logs (Anti-Fuga System)
CREATE TABLE IF NOT EXISTS sentinel_unparsed_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    log_type VARCHAR NOT NULL,
    filename VARCHAR NOT NULL,
    raw_line TEXT NOT NULL,
    attempted_parsers VARCHAR,
    error_message VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_unparsed_timestamp ON sentinel_unparsed_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_unparsed_log_type ON sentinel_unparsed_logs(log_type);

-- ============================================================================
-- 3. COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE sentinel_bank_transactions IS 'Transações bancárias: depósitos, saques e transferências entre jogadores';
COMMENT ON TABLE sentinel_mechanic_services IS 'Serviços de mecânico: compra, instalação, reparo e remoção de peças';
COMMENT ON TABLE sentinel_bank_cards IS 'Gestão de cartões bancários: compra e destruição de cartões Starter, Gold e Classic';
COMMENT ON TABLE sentinel_unparsed_logs IS 'Sistema anti-fuga: logs que não foram reconhecidos por nenhum parser';

COMMENT ON COLUMN sentinel_economy_trades.item_health IS 'Durabilidade do item vendido (0-100)';
COMMENT ON COLUMN sentinel_economy_trades.item_uses IS 'Usos/munição restantes no item';
COMMENT ON COLUMN sentinel_economy_trades.is_mechanic_service IS 'Flag para diferenciar serviços de mecânico de compras normais';
COMMENT ON COLUMN sentinel_bank_transactions.fee IS 'Taxa cobrada na transação (gross_amount - net_amount)';
