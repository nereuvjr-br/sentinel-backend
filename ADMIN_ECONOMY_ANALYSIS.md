# Análise de Comandos Admin com Impacto Econômico

## 🔍 Comandos Identificados nos Logs

### 1. **SpawnItem** (ALTO IMPACTO ECONÔMICO) 🚨
**Formato:** `SpawnItem <item> <quantidade> Location "<coords>" [StackCount <valor>]`

**Exemplos Reais:**
```
SpawnItem Cash 1 StackCount 5000 Location "149468.109 -283452.656 20832.590"
SpawnItem Weapon_Block21 1 Location "149468.109 -283452.656 20832.590"
SpawnItem Magazine_Block21 3 Location "149468.109 -283452.656 20832.590"
SpawnItem Cal_45_Ammobox 3 Location "149468.109 -283452.656 20832.590"
```

**Impacto Econômico:**
- ⚠️ **CRÍTICO**: Spawn de Cash (dinheiro direto)
- ⚠️ **ALTO**: Spawn de armas valiosas (Block21, AS Val, AKS-74U)
- ⚠️ **MÉDIO**: Spawn de munição, comida, equipamentos

**Dados Extraíveis:**
- Item Class
- Quantidade
- Stack Count (para Cash/Ammo)
- Localização
- Admin responsável
- Timestamp

---

### 2. **DestroyAllItemsWithinRadius** (MÉDIO IMPACTO) ⚠️
**Formato:** `DestroyAllItemsWithinRadius <item> <radius>`

**Exemplos Reais:**
```
DestroyAllItemsWithinRadius Inmate_Pants_01_Forest_DigitalDeluxe 100000000
DestroyAllItemsWithinRadius Danny_Trejo_Boots_01 100000000
DestroyAllItemsWithinRadius Weapon_DEagle_50 100000000
```

**Impacto Econômico:**
- Remove itens do mundo (pode afetar economia se for item valioso)
- Geralmente usado para limpar itens de eventos/DLC

**Dados Extraíveis:**
- Item Class
- Radius
- Admin responsável

---

### 3. **Teleport** (BAIXO IMPACTO DIRETO) ℹ️
**Formato:** `teleport <x> <y> <z> <steamid>`

**Exemplo Real:**
```
teleport -434430.50000000 -678401.18800000 332.15000000 76561198066139199
```

**Impacto Econômico:**
- Indireto: Admin pode teleportar para dar itens
- Útil para rastrear atividade de admin

---

## 🎯 PROPOSTA: Nova Tabela `sentinel_admin_economy_actions`

### Objetivo
Rastrear especificamente comandos de admin que impactam a economia do servidor, permitindo:
- Auditoria de spawns de dinheiro
- Detecção de abuso de admin
- Análise de inflação causada por spawns
- Histórico completo de intervenções econômicas

### Estrutura Proposta

```sql
CREATE TABLE sentinel_admin_economy_actions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    
    -- Admin Info
    admin_steam_id VARCHAR(255) NOT NULL,
    admin_name VARCHAR(255) NOT NULL,
    admin_game_id VARCHAR(50),
    
    -- Action Details
    action_type VARCHAR(50) NOT NULL,  -- spawn_item, spawn_cash, destroy_item, give_money
    raw_command TEXT NOT NULL,
    
    -- Economic Impact
    item_class VARCHAR(255),
    item_quantity INTEGER,
    stack_count INTEGER,              -- Para Cash/Ammo
    economic_value DOUBLE PRECISION,  -- Valor estimado em dinheiro
    
    -- Target (se houver)
    target_steam_id VARCHAR(255),
    target_name VARCHAR(255),
    
    -- Location
    location JSONB,
    
    -- Impact Classification
    impact_level VARCHAR(20),  -- critical, high, medium, low
    is_cash_spawn BOOLEAN DEFAULT FALSE,
    is_weapon_spawn BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    is_automated BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Índices
```sql
CREATE INDEX idx_admin_eco_timestamp ON sentinel_admin_economy_actions(timestamp DESC);
CREATE INDEX idx_admin_eco_admin ON sentinel_admin_economy_actions(admin_steam_id);
CREATE INDEX idx_admin_eco_action ON sentinel_admin_economy_actions(action_type);
CREATE INDEX idx_admin_eco_impact ON sentinel_admin_economy_actions(impact_level);
CREATE INDEX idx_admin_eco_cash ON sentinel_admin_economy_actions(is_cash_spawn) WHERE is_cash_spawn = TRUE;
CREATE INDEX idx_admin_eco_item ON sentinel_admin_economy_actions(item_class);
```

---

## 📊 Classificação de Impacto Econômico

### CRITICAL (Crítico) 🔴
- Spawn de Cash (dinheiro direto)
- Spawn de Gold
- Comandos que adicionam >100k de valor

**Exemplo:**
```
SpawnItem Cash 1 StackCount 50000  → CRITICAL (50k em dinheiro)
```

### HIGH (Alto) 🟠
- Spawn de armas raras/caras (Block21, AS Val, SVD)
- Spawn de veículos
- Spawn de equipamento militar avançado

**Exemplo:**
```
SpawnItem Weapon_Block21 1  → HIGH (~30k valor estimado)
```

### MEDIUM (Médio) 🟡
- Spawn de munição em grande quantidade
- Spawn de comida/água
- Spawn de equipamento básico

**Exemplo:**
```
SpawnItem Magazine_AKS_74U 3 StackCount 30  → MEDIUM
```

### LOW (Baixo) 🟢
- Destroy de itens comuns
- Teleports
- Comandos administrativos sem impacto direto

---

## 🔧 Parser Enhancements

### Atualizar `AdminParserV2`

Adicionar detecção de impacto econômico:

```python
class AdminParserV2:
    # Tabela de valores estimados (em dinheiro)
    ITEM_VALUES = {
        'Cash': 1,  # Multiplicador direto
        'Gold': 100,  # 1 gold = 100 cash
        'Weapon_Block21': 30000,
        'Weapon_AS_Val': 25000,
        'Weapon_AKS_74U': 20000,
        'Weapon_MosinNagant': 15000,
        # ... mais itens
    }
    
    # Armas de alto valor
    HIGH_VALUE_WEAPONS = [
        'Weapon_Block21', 'Weapon_AS_Val', 'Weapon_SVD',
        'Weapon_VSS', 'Weapon_AKS_74U', 'Weapon_M82A1'
    ]
    
    @staticmethod
    def classify_economic_impact(item_class, quantity, stack_count):
        """Classifica o impacto econômico de um spawn"""
        
        # Cash direto
        if item_class == 'Cash':
            value = stack_count or quantity
            if value >= 50000:
                return 'critical', value
            elif value >= 10000:
                return 'high', value
            else:
                return 'medium', value
        
        # Armas valiosas
        if item_class in HIGH_VALUE_WEAPONS:
            base_value = ITEM_VALUES.get(item_class, 10000)
            total_value = base_value * quantity
            if total_value >= 50000:
                return 'critical', total_value
            else:
                return 'high', total_value
        
        # Outros itens
        return 'low', 0
```

---

## 📈 Casos de Uso

### 1. Auditoria de Spawns de Dinheiro
```sql
SELECT 
    admin_name,
    SUM(stack_count) as total_cash_spawned,
    COUNT(*) as spawn_count,
    MAX(timestamp) as last_spawn
FROM sentinel_admin_economy_actions
WHERE is_cash_spawn = TRUE
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY admin_name
ORDER BY total_cash_spawned DESC;
```

### 2. Detecção de Abuso
```sql
-- Admins que spawnaram >500k em uma semana
SELECT 
    admin_name,
    SUM(economic_value) as total_value,
    COUNT(*) as action_count
FROM sentinel_admin_economy_actions
WHERE impact_level IN ('critical', 'high')
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY admin_name
HAVING SUM(economic_value) > 500000
ORDER BY total_value DESC;
```

### 3. Análise de Inflação
```sql
-- Valor total injetado na economia por dia
SELECT 
    DATE(timestamp) as date,
    SUM(economic_value) as total_injected,
    COUNT(*) as actions
FROM sentinel_admin_economy_actions
WHERE action_type = 'spawn_item'
  AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

### 4. Top Itens Spawnados
```sql
SELECT 
    item_class,
    SUM(item_quantity) as total_spawned,
    AVG(economic_value) as avg_value,
    COUNT(DISTINCT admin_steam_id) as admin_count
FROM sentinel_admin_economy_actions
WHERE action_type = 'spawn_item'
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY item_class
ORDER BY total_spawned DESC
LIMIT 20;
```

---

## 🚨 Sistema de Alertas Automáticos

### Alertas a Criar em `sentinel_economy_alerts`

1. **admin_cash_spawn_excessive**
   - Trigger: Admin spawnou >100k em cash em 1 hora
   - Severity: CRITICAL

2. **admin_weapon_flood**
   - Trigger: Admin spawnou >10 armas de alto valor em 1 hora
   - Severity: HIGH

3. **admin_inflation_spike**
   - Trigger: Valor total spawnado aumentou >200% vs. média
   - Severity: HIGH

4. **admin_suspicious_pattern**
   - Trigger: Mesmo admin spawna itens e teleporta para mesmo jogador
   - Severity: MEDIUM

---

## 💡 Integração com Sistema Existente

### Fluxo de Dados

```
Admin Log → AdminParserV2 → sentinel_admin_commands (existente)
                          ↓
                   Análise Econômica
                          ↓
            sentinel_admin_economy_actions (NOVA)
                          ↓
                  Cálculo de Impacto
                          ↓
            sentinel_economy_alerts (se necessário)
```

### Enriquecimento de Dados

Após salvar em `sentinel_admin_economy_actions`, atualizar:
- `sentinel_economy_alerts` (se spawn suspeito)
- Estatísticas agregadas de admin
- Dashboard de atividade econômica

---

## 📊 Resumo Executivo

**Problema Identificado:**
- Comandos de admin podem injetar valor ilimitado na economia
- Atualmente não há rastreamento específico de impacto econômico
- Impossível detectar abuso de admin ou inflação causada por spawns

**Solução Proposta:**
- Nova tabela `sentinel_admin_economy_actions`
- Parser aprimorado com classificação de impacto
- Sistema de alertas automáticos
- Dashboards de auditoria

**Benefícios:**
- ✅ Auditoria completa de intervenções econômicas
- ✅ Detecção de abuso de admin
- ✅ Análise de inflação causada por spawns
- ✅ Transparência administrativa
- ✅ Histórico completo de ações econômicas

**Impacto Esperado:**
- Redução de 90% em spawns não autorizados
- Detecção automática de padrões suspeitos
- Confiança aumentada na economia do servidor
