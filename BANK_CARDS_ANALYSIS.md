# ✅ Análise: Captura de Registros de Cards Bancários

## 📊 Status Atual

### ✅ **JÁ IMPLEMENTADO E FUNCIONANDO**

A captura de eventos de cards bancários **já está completamente implementada** no sistema!

---

## 🎯 Tabela: `sentinel_bank_cards`

### Estrutura Atual
```sql
CREATE TABLE sentinel_bank_cards (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    
    -- Player Info
    steam_id VARCHAR(255) NOT NULL,
    player_name VARCHAR(255) NOT NULL,
    account_number VARCHAR(255) NOT NULL,
    
    -- Card Details
    action VARCHAR(50) NOT NULL,        -- "purchased", "manually destroyed"
    card_type VARCHAR(255) NOT NULL,    -- "Starter card", "Gold card", "Classic card"
    
    -- Purchase Details
    free_renewal BOOLEAN,
    new_balance DOUBLE PRECISION,
    
    -- Destruction Details
    destroyed_account VARCHAR(255),
    
    -- Location
    pos_x DOUBLE PRECISION NOT NULL,
    pos_y DOUBLE PRECISION NOT NULL,
    pos_z DOUBLE PRECISION NOT NULL
);
```

### Índices Existentes
- `idx_bank_cards_timestamp` (timestamp)
- `idx_bank_cards_steam_id` (steam_id)
- `idx_bank_cards_account` (account_number)
- `idx_bank_cards_action` (action)
- `idx_bank_cards_type` (card_type)

---

## 🔍 Eventos Capturados

### 1. **Compra de Cartão** ✅
**Formato do Log:**
```
2025.12.26-16.08.00: [Bank] Player(ID:76561198066139199)(Account Number:12345) 
purchased Starter card (free renewal: yes), new account balance is 95000 credits, 
at X=-434430.50 Y=-678401.19 Z=332.15.
```

**Dados Extraídos:**
- ✅ Timestamp
- ✅ SteamID e Nome do jogador
- ✅ Número da conta
- ✅ Tipo de cartão (Starter, Gold, Classic)
- ✅ Renovação grátis (yes/no)
- ✅ Novo saldo da conta
- ✅ Localização (X, Y, Z)

---

### 2. **Destruição Manual de Cartão** ✅
**Formato do Log:**
```
2025.12.26-16.10.00: [Bank] Player(ID:76561198066139199)(Account Number:12345) 
manually destroyed Gold card belonging to Account Number:67890, 
at X=-434430.50 Y=-678401.19 Z=332.15.
```

**Dados Extraídos:**
- ✅ Timestamp
- ✅ SteamID e Nome do jogador
- ✅ Número da conta do jogador
- ✅ Tipo de cartão destruído
- ✅ Número da conta do cartão destruído
- ✅ Localização (X, Y, Z)

---

## 📈 Queries Úteis

### 1. Histórico de Cards por Jogador
```sql
SELECT 
    timestamp,
    action,
    card_type,
    account_number,
    new_balance
FROM sentinel_bank_cards
WHERE steam_id = '76561198066139199'
ORDER BY timestamp DESC;
```

### 2. Cards Comprados (Últimos 7 dias)
```sql
SELECT 
    player_name,
    card_type,
    free_renewal,
    new_balance,
    timestamp
FROM sentinel_bank_cards
WHERE action = 'purchased'
  AND timestamp >= NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

### 3. Cards Destruídos (Suspeito)
```sql
SELECT 
    player_name,
    card_type,
    destroyed_account,
    timestamp,
    pos_x, pos_y, pos_z
FROM sentinel_bank_cards
WHERE action = 'manually destroyed'
ORDER BY timestamp DESC;
```

### 4. Estatísticas por Tipo de Card
```sql
SELECT 
    card_type,
    COUNT(*) as total_purchases,
    COUNT(*) FILTER (WHERE free_renewal = TRUE) as with_free_renewal,
    AVG(new_balance) as avg_balance_after
FROM sentinel_bank_cards
WHERE action = 'purchased'
GROUP BY card_type
ORDER BY total_purchases DESC;
```

### 5. Jogadores com Múltiplos Cards
```sql
SELECT 
    steam_id,
    player_name,
    COUNT(DISTINCT account_number) as card_count,
    array_agg(DISTINCT card_type) as card_types
FROM sentinel_bank_cards
WHERE action = 'purchased'
GROUP BY steam_id, player_name
HAVING COUNT(DISTINCT account_number) > 1
ORDER BY card_count DESC;
```

---

## 🔗 Integração com `sentinel_account_registry`

### Atualização Automática de Flags
Quando um card é comprado ou destruído, podemos atualizar a tabela `sentinel_account_registry`:

```sql
-- Atualizar flag has_card quando comprado
UPDATE sentinel_account_registry
SET has_card = TRUE,
    card_type = 'Starter card'
WHERE account_number = '12345';

-- Atualizar flag has_card quando destruído
UPDATE sentinel_account_registry
SET has_card = FALSE,
    card_type = NULL
WHERE account_number = '67890';
```

---

## 💡 Melhorias Sugeridas (Opcional)

### 1. **Adicionar Campo: `card_price`**
Capturar o preço pago pelo cartão (se disponível nos logs)

```sql
ALTER TABLE sentinel_bank_cards
ADD COLUMN card_price DOUBLE PRECISION;
```

### 2. **Adicionar Campo: `previous_balance`**
Saldo anterior à compra (para calcular custo exato)

```sql
ALTER TABLE sentinel_bank_cards
ADD COLUMN previous_balance DOUBLE PRECISION;
```

### 3. **Trigger para Atualizar `account_registry`**
Criar trigger automático para sincronizar flags:

```sql
CREATE OR REPLACE FUNCTION update_account_card_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.action = 'purchased' THEN
        UPDATE sentinel_account_registry
        SET has_card = TRUE,
            card_type = NEW.card_type
        WHERE account_number = NEW.account_number;
    ELSIF NEW.action = 'manually destroyed' THEN
        UPDATE sentinel_account_registry
        SET has_card = FALSE,
            card_type = NULL
        WHERE account_number = NEW.destroyed_account;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_account_card
AFTER INSERT ON sentinel_bank_cards
FOR EACH ROW
EXECUTE FUNCTION update_account_card_status();
```

---

## 🚨 Alertas Sugeridos

### 1. **card_destruction_spree**
- **Trigger:** Jogador destruiu >5 cards em 1 hora
- **Severity:** MEDIUM
- **Motivo:** Possível griefing ou bug

### 2. **multiple_cards_same_account**
- **Trigger:** Mesma conta comprou >3 cards
- **Severity:** LOW
- **Motivo:** Possível desperdício ou teste

### 3. **card_purchase_without_balance**
- **Trigger:** Comprou card mas saldo final < preço do card
- **Severity:** HIGH
- **Motivo:** Possível exploit

---

## 📊 Dashboard Sugerido

### Card: "Bank Card Activity"
- Total de cards comprados (hoje)
- Total de cards destruídos (hoje)
- Tipo de card mais popular
- Jogadores com mais cards

### Card: "Card Destruction Log"
- Lista de destruições recentes
- Jogador, tipo de card, timestamp
- Localização da destruição

---

## ✅ Checklist de Verificação

### Captura de Dados
- [x] Compra de cartão (purchase)
- [x] Destruição de cartão (destroy)
- [x] SteamID e nome do jogador
- [x] Número da conta
- [x] Tipo de cartão
- [x] Renovação grátis
- [x] Novo saldo
- [x] Localização

### Integração
- [x] Parser implementado (`EconomyParserV2`)
- [x] Regex funcionando
- [x] Tabela criada (`sentinel_bank_cards`)
- [x] Índices otimizados
- [ ] Trigger para `account_registry` (opcional)
- [ ] Alertas automáticos (opcional)

### Queries
- [x] Histórico por jogador
- [x] Cards comprados
- [x] Cards destruídos
- [x] Estatísticas por tipo
- [x] Múltiplos cards

---

## 🎉 Conclusão

**Status:** ✅ **COMPLETAMENTE IMPLEMENTADO**

A captura de registros de cards bancários está **100% funcional** e capturando todos os dados relevantes:

1. ✅ Compras de cartões
2. ✅ Destruições de cartões
3. ✅ Todos os metadados (tipo, renovação, saldo, localização)
4. ✅ Índices otimizados
5. ✅ Queries prontas para uso

**Próximos Passos (Opcional):**
- Criar trigger para sincronizar com `account_registry`
- Implementar alertas automáticos
- Adicionar dashboard de cards no frontend

**Não há necessidade de criar novas tabelas ou parsers. O sistema já está capturando tudo!** ✅
