# Análise de Logs Não Processados - Sugestões de Novas Tabelas

## 📊 Status Atual
**Tabelas Existentes:** 19
**Tipos de Logs Disponíveis:** 16
**Logs NÃO Processados:** 7

---

## 🔍 Logs Identificados e Análise

### 1. ✅ **LOOT LOGS** (Alta Prioridade)
**Arquivo:** `loot_*.log`  
**Tamanho Médio:** 1-3 MB (MUITO VOLUMOSO)  
**Status:** ❌ NÃO PROCESSADO

**Conteúdo Identificado:**
- Logs de sistema sobre configuração de spawn de itens
- Informações sobre cooldown groups
- Items desabilitados para spawn

**Valor Administrativo:** ⭐⭐ (Baixo)
- Logs técnicos de configuração do servidor
- Não contém ações de jogadores
- **RECOMENDAÇÃO:** Ignorar por enquanto (não tem valor para análise de jogadores)

---

### 2. ✅ **QUEST LOGS** (Prioridade ALTA)
**Arquivo:** `quests_*.log`  
**Tamanho Médio:** 100-1000 bytes  
**Status:** ❌ NÃO PROCESSADO

**Formato Identificado:**
```
2025.12.26-17.04.13: [LogQuestStatus] IamNeoN (193, 76561199261697866) completed quest Quest_GeneralGoods_Tier0_FindAnOutpost
```

**Dados Extraíveis:**
- Timestamp
- Player Name
- Game ID
- SteamID
- Quest Name
- Status (completed, started, failed)

**Valor Administrativo:** ⭐⭐⭐⭐⭐ (MUITO ALTO)
- Rastreamento de progressão de jogadores
- Identificação de quests problemáticas (baixa taxa de conclusão)
- Detecção de exploits (conclusão muito rápida)
- Métricas de engajamento

**TABELA SUGERIDA:** `sentinel_quest_events`

---

### 3. ✅ **RAID PROTECTION LOGS** (Prioridade MÉDIA)
**Arquivo:** `raid_protection_*.log`  
**Tamanho Médio:** 252 bytes (fixo)  
**Status:** ❌ NÃO PROCESSADO

**Conteúdo Identificado:**
```
2025.12.26-16.01.08: Parsing 'RaidTimes.json'
2025.12.26-16.01.08: Success!
```

**Valor Administrativo:** ⭐ (Muito Baixo)
- Apenas logs de carregamento de configuração
- **RECOMENDAÇÃO:** Ignorar (sem dados de jogadores)

---

### 4. ✅ **ARMOR ABSORPTION LOGS** (Prioridade BAIXA)
**Arquivo:** `armor_absorption_*.log`  
**Tamanho Médio:** 100 bytes (vazio)  
**Status:** ❌ NÃO PROCESSADO

**Valor Administrativo:** ⭐ (Muito Baixo)
- Arquivos vazios
- **RECOMENDAÇÃO:** Ignorar

---

### 5. ✅ **EVENT KILL LOGS** (Prioridade BAIXA)
**Arquivo:** `event_kill_*.log`  
**Tamanho Médio:** 100 bytes (vazio)  
**Status:** ❌ NÃO PROCESSADO

**Observação:** Kills em eventos já são capturados em `sentinel_kills` (campo `is_event`)
**RECOMENDAÇÃO:** Ignorar (redundante)

---

### 6. ✅ **SENTRY LOGS** (Prioridade BAIXA)
**Arquivo:** `sentry_*.log`  
**Tamanho Médio:** 100 bytes (vazio)  
**Status:** ❌ NÃO PROCESSADO

**Valor Administrativo:** ⭐ (Muito Baixo)
- Arquivos vazios
- **RECOMENDAÇÃO:** Ignorar

---

### 7. ✅ **SERVER NOTIFICATIONS LOGS** (Prioridade BAIXA)
**Arquivo:** `server_notifications_*.log`  
**Tamanho Médio:** 100 bytes (vazio)  
**Status:** ❌ NÃO PROCESSADO

**Valor Administrativo:** ⭐ (Muito Baixo)
- Arquivos vazios
- **RECOMENDAÇÃO:** Ignorar

---

## 🎯 RECOMENDAÇÕES FINAIS

### Tabelas a Criar (1 Tabela Nova)

#### 1. **`sentinel_quest_events`** ⭐⭐⭐⭐⭐ PRIORIDADE MÁXIMA

**Justificativa:**
- Dados valiosos sobre progressão de jogadores
- Permite identificar quests problemáticas
- Detecta possíveis exploits
- Métricas de engajamento e retenção

**Estrutura Proposta:**
```sql
CREATE TABLE sentinel_quest_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    steam_id VARCHAR(255) NOT NULL,
    player_name VARCHAR(255) NOT NULL,
    game_id INTEGER,
    quest_name VARCHAR(255) NOT NULL,
    quest_status VARCHAR(50) NOT NULL,  -- completed, started, failed, abandoned
    location JSONB,  -- Se disponível
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Campos:**
- `id`: PK
- `timestamp`: Quando ocorreu
- `steam_id`: SteamID do jogador
- `player_name`: Nome do jogador
- `game_id`: ID de jogo
- `quest_name`: Nome da quest
- `quest_status`: Status (completed, started, failed)
- `location`: Coordenadas (se disponível)
- `processed_at`: Timestamp de processamento

**Índices:**
- `idx_quest_timestamp`
- `idx_quest_steam_id`
- `idx_quest_name`
- `idx_quest_status`

**Casos de Uso:**
1. **Dashboard de Quests:** Mostrar quests mais populares/difíceis
2. **Player Progression:** Rastrear progresso individual
3. **Anti-Exploit:** Detectar conclusões suspeitas (muito rápidas)
4. **Balanceamento:** Identificar quests com baixa taxa de conclusão

---

## 📈 Análise de Dados Atuais

### Dados Já Extraídos mas Subutilizados

#### 1. **Account Numbers** (Economy)
**Onde:** `sentinel_economy_balances`, `sentinel_bank_transactions`, `sentinel_bank_cards`  
**Oportunidade:** Criar tabela `sentinel_player_accounts` para consolidar informações de contas

**Benefícios:**
- Histórico de contas por jogador
- Rastreamento de múltiplas contas
- Detecção de transferências suspeitas entre contas

#### 2. **Trader Funds** (Economy)
**Onde:** `sentinel_economy_balances.trader_funds`  
**Oportunidade:** Criar tabela `sentinel_trader_economy` para rastrear economia dos NPCs

**Benefícios:**
- Monitorar inflação/deflação
- Identificar traders "quebrados" (sem fundos)
- Balanceamento econômico

#### 3. **Item Health/Uses** (Economy)
**Onde:** `sentinel_economy_trades.item_health`, `item_uses`  
**Oportunidade:** Criar tabela `sentinel_item_durability` para análise de desgaste

**Benefícios:**
- Identificar itens vendidos "quebrados"
- Análise de economia de reparos
- Detecção de exploits de durabilidade

---

## 🚀 Plano de Implementação Sugerido

### Fase 1: Quest System (AGORA)
- [ ] Criar `sentinel_quest_events`
- [ ] Implementar `QuestParserV2`
- [ ] Integrar ao `sentinel_v2.py`
- [ ] Criar migração SQL

### Fase 2: Consolidação de Dados Existentes (FUTURO)
- [ ] `sentinel_player_accounts` (consolidação de contas)
- [ ] `sentinel_trader_economy` (economia de NPCs)
- [ ] `sentinel_item_durability` (análise de desgaste)

### Fase 3: Análise Avançada (FUTURO)
- [ ] Views materializadas para dashboards
- [ ] Triggers para alertas automáticos
- [ ] Stored procedures para relatórios

---

## 📝 Resumo Executivo

**Logs Valiosos Não Processados:** 1 (Quests)  
**Logs Sem Valor:** 6 (Loot config, Armor, Sentry, etc)  
**Tabelas Recomendadas:** 1 nova tabela  
**Prioridade:** ALTA para Quest Events  

**Impacto Esperado:**
- ✅ Melhor entendimento do engajamento dos jogadores
- ✅ Detecção de exploits em quests
- ✅ Métricas de progressão e retenção
- ✅ Balanceamento de conteúdo baseado em dados
