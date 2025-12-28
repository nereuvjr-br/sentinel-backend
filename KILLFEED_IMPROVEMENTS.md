# 🎯 Análise e Melhorias - Sistema de Killfeeds

## 📊 Status Atual

### ✅ Tabela Existente: `sentinel_kills`

**Campos Capturados:**
- ✅ Timestamp
- ✅ Killer (ID, Name, Location Server/Client, Immortal)
- ✅ Victim (ID, Name, Location)
- ✅ Weapon
- ✅ Distance (oficial do log)
- ✅ Is Event (kill em evento)
- ✅ Time of Day
- ✅ Violation Score (anti-cheat)

---

## 🔍 Dados Disponíveis nos Logs (Não Capturados)

### Exemplo de Log Completo:
```json
{
  "Killer": {
    "ServerLocation": {"X": 232767.36, "Y": -35077.35, "Z": 26512.69},
    "ClientLocation": {"X": 232767.36, "Y": -35077.35, "Z": 26512.69},
    "IsInGameEvent": false,
    "ProfileName": "Scooby",
    "UserId": "76561198965481578",
    "HasImmortality": false
  },
  "Victim": {
    "ServerLocation": {"X": 242812.19, "Y": -30699.12, "Z": 24707.17},
    "ProfileName": "MAIA",
    "UserId": "76561199625739748"
  },
  "Weapon": "Weapon_AKS_74U_C [Projectile]",
  "TimeOfDay": "05:11:12"
}
```

### ❌ Dados NÃO Capturados (Oportunidades):

1. **Weapon Details** (Detalhes da Arma)
   - Weapon Class (ex: `Weapon_AKS_74U_C`)
   - Damage Type (`[Projectile]`, `[Melee]`, `[Explosion]`)
   - Atualmente salvamos tudo junto: `"Weapon_AKS_74U_C [Projectile]"`

2. **Kill Context** (Contexto do Kill)
   - Headshot? (não disponível nos logs)
   - Body Part Hit? (não disponível)
   - Killer Health? (não disponível)
   - Victim Health? (não disponível)

3. **Environmental Data** (Dados Ambientais)
   - Weather? (não disponível)
   - Visibility? (não disponível)
   - Terrain Type? (poderia inferir de coordenadas)

4. **Squad Information** (Informação de Squad)
   - Killer Squad (não disponível nos logs)
   - Victim Squad (não disponível)
   - Team Kill? (poderia inferir se implementarmos squads)

---

## 💡 Melhorias Propostas

### 1. **Separar Weapon Class e Damage Type** ⭐⭐⭐⭐⭐

**Problema Atual:**
```sql
weapon = "Weapon_AKS_74U_C [Projectile]"
```

**Proposta:**
```sql
weapon_class = "Weapon_AKS_74U_C"
damage_type = "Projectile"  -- Projectile, Melee, Explosion, Fall, Drowning
```

**Benefícios:**
- Estatísticas por tipo de arma
- Estatísticas por tipo de dano
- Queries mais eficientes
- Análise de meta (armas mais usadas)

**Implementação:**
```python
def parse_weapon(weapon_str: str) -> tuple:
    """
    Parse weapon string into class and damage type
    Ex: "Weapon_AKS_74U_C [Projectile]" -> ("Weapon_AKS_74U_C", "Projectile")
    """
    import re
    match = re.match(r'(.+?)\s*\[(.+?)\]', weapon_str)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return weapon_str, "Unknown"
```

---

### 2. **Adicionar Weapon Category** ⭐⭐⭐⭐

**Objetivo:** Categorizar armas para análise

**Categorias Sugeridas:**
- `Assault Rifle` (AK, M4, etc)
- `SMG` (MP5, MAC10, etc)
- `Sniper Rifle` (SVD, Mosin, etc)
- `Pistol` (Glock, Desert Eagle, etc)
- `Shotgun` (Pump, Auto, etc)
- `Melee` (Knife, Axe, etc)
- `Explosive` (C4, Grenade, etc)
- `Vehicle` (Car, Heli, etc)
- `Environment` (Fall, Drowning, etc)
- `NPC` (Guard, Puppet, etc)

**Implementação:**
```python
WEAPON_CATEGORIES = {
    'Weapon_AKS_74U': 'Assault Rifle',
    'Weapon_AK47': 'Assault Rifle',
    'Weapon_M4A1': 'Assault Rifle',
    'Weapon_MP5': 'SMG',
    'Weapon_MAC10': 'SMG',
    'Weapon_SVD': 'Sniper Rifle',
    'Weapon_MosinNagant': 'Sniper Rifle',
    'Weapon_Glock': 'Pistol',
    'Weapon_DEagle': 'Pistol',
    # ... mais armas
}

def get_weapon_category(weapon_class: str) -> str:
    for key, category in WEAPON_CATEGORIES.items():
        if key in weapon_class:
            return category
    return 'Other'
```

---

### 3. **Detectar NPCs Automaticamente** ⭐⭐⭐⭐⭐

**Problema:** Kills de NPCs (Guards, Puppets) não são diferenciados

**Solução:** Detectar padrões de nome

```python
def is_npc(name: str, user_id: str) -> tuple:
    """
    Detecta se é NPC e retorna (is_npc, npc_type)
    """
    npc_patterns = {
        'BP_Guard': 'Guard',
        'BP_Puppet': 'Puppet',
        'BP_Mech': 'Mech',
        'BP_Animal': 'Animal',
        'BOT_': 'Bot',
    }
    
    for pattern, npc_type in npc_patterns.items():
        if pattern in name:
            return True, npc_type
    
    # SteamID inválido também indica NPC
    if not user_id or len(user_id) < 10:
        return True, 'Unknown'
    
    return False, None
```

**Novos Campos:**
- `killer_is_npc` (BOOLEAN)
- `killer_npc_type` (VARCHAR) - Guard, Puppet, etc
- `victim_is_npc` (BOOLEAN)
- `victim_npc_type` (VARCHAR)

---

### 4. **Calcular Kill Streaks** ⭐⭐⭐⭐

**Objetivo:** Rastrear sequências de kills

**Implementação:** View Materializada

```sql
CREATE MATERIALIZED VIEW sentinel_kill_streaks AS
WITH ranked_kills AS (
    SELECT 
        killer_id,
        killer_name,
        timestamp,
        LAG(timestamp) OVER (PARTITION BY killer_id ORDER BY timestamp) as prev_kill_time
    FROM sentinel_kills
    WHERE killer_id IS NOT NULL
      AND victim_is_npc = FALSE  -- Apenas kills de players
),
streaks AS (
    SELECT 
        killer_id,
        killer_name,
        timestamp,
        CASE 
            WHEN prev_kill_time IS NULL THEN 1
            WHEN timestamp - prev_kill_time <= INTERVAL '5 minutes' THEN 0
            ELSE 1
        END as is_new_streak
    FROM ranked_kills
),
streak_groups AS (
    SELECT 
        killer_id,
        killer_name,
        timestamp,
        SUM(is_new_streak) OVER (PARTITION BY killer_id ORDER BY timestamp) as streak_id
    FROM streaks
)
SELECT 
    killer_id,
    killer_name,
    streak_id,
    COUNT(*) as kill_count,
    MIN(timestamp) as streak_start,
    MAX(timestamp) as streak_end,
    MAX(timestamp) - MIN(timestamp) as duration
FROM streak_groups
GROUP BY killer_id, killer_name, streak_id
HAVING COUNT(*) >= 3  -- Apenas streaks de 3+ kills
ORDER BY kill_count DESC;
```

---

### 5. **Adicionar Revenge Kills** ⭐⭐⭐

**Objetivo:** Detectar quando vítima mata seu killer anterior

```sql
-- Query para detectar revenge kills
WITH recent_deaths AS (
    SELECT 
        victim_id,
        killer_id,
        timestamp,
        LEAD(timestamp) OVER (PARTITION BY victim_id ORDER BY timestamp) as next_event
    FROM sentinel_kills
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
)
SELECT 
    k.timestamp as revenge_time,
    k.killer_name as avenger,
    k.victim_name as original_killer,
    rd.timestamp as original_death,
    k.timestamp - rd.timestamp as time_to_revenge
FROM sentinel_kills k
JOIN recent_deaths rd ON 
    k.killer_id = rd.victim_id AND 
    k.victim_id = rd.killer_id AND
    k.timestamp > rd.timestamp AND
    k.timestamp <= rd.next_event
WHERE k.timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY k.timestamp DESC;
```

**Novo Campo:**
- `is_revenge_kill` (BOOLEAN)
- `revenge_for_kill_id` (INTEGER FK)

---

### 6. **Hotspots de Kills** ⭐⭐⭐⭐

**Objetivo:** Identificar áreas com mais PvP

```sql
-- Agrupar kills por grid (100m x 100m)
SELECT 
    FLOOR(killer_loc_server->>'X'::float / 10000) * 10000 as grid_x,
    FLOOR(killer_loc_server->>'Y'::float / 10000) * 10000 as grid_y,
    COUNT(*) as kill_count,
    COUNT(DISTINCT killer_id) as unique_killers,
    AVG(distance) as avg_distance
FROM sentinel_kills
WHERE timestamp >= NOW() - INTERVAL '7 days'
  AND victim_is_npc = FALSE
GROUP BY grid_x, grid_y
HAVING COUNT(*) > 10
ORDER BY kill_count DESC
LIMIT 20;
```

---

### 7. **Kill Efficiency Metrics** ⭐⭐⭐⭐

**Objetivo:** Métricas de eficiência por jogador

```sql
CREATE VIEW sentinel_player_kill_stats AS
SELECT 
    killer_id,
    killer_name,
    
    -- Basic Stats
    COUNT(*) as total_kills,
    COUNT(*) FILTER (WHERE victim_is_npc = FALSE) as player_kills,
    COUNT(*) FILTER (WHERE victim_is_npc = TRUE) as npc_kills,
    
    -- Weapon Stats
    COUNT(DISTINCT weapon_class) as weapons_used,
    MODE() WITHIN GROUP (ORDER BY weapon_class) as favorite_weapon,
    
    -- Distance Stats
    AVG(distance) as avg_kill_distance,
    MAX(distance) as longest_kill,
    
    -- Time Stats
    COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 0 AND 6) as night_kills,
    COUNT(*) FILTER (WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 6 AND 18) as day_kills,
    
    -- Anti-Cheat
    AVG(violation_score) as avg_violation_score,
    MAX(violation_score) as max_violation_score,
    
    -- Activity
    MIN(timestamp) as first_kill,
    MAX(timestamp) as last_kill
    
FROM sentinel_kills
WHERE killer_id IS NOT NULL
GROUP BY killer_id, killer_name;
```

---

## 🗄️ Estrutura de Tabela Melhorada

### Novos Campos Propostos:

```sql
ALTER TABLE sentinel_kills
ADD COLUMN weapon_class VARCHAR(255),
ADD COLUMN damage_type VARCHAR(50),
ADD COLUMN weapon_category VARCHAR(50),

ADD COLUMN killer_is_npc BOOLEAN DEFAULT FALSE,
ADD COLUMN killer_npc_type VARCHAR(50),
ADD COLUMN victim_is_npc BOOLEAN DEFAULT FALSE,
ADD COLUMN victim_npc_type VARCHAR(50),

ADD COLUMN is_revenge_kill BOOLEAN DEFAULT FALSE,
ADD COLUMN revenge_for_kill_id INTEGER REFERENCES sentinel_kills(id),

ADD COLUMN kill_streak_id INTEGER,
ADD COLUMN is_headshot BOOLEAN,  -- Se disponível no futuro

ADD COLUMN grid_x INTEGER,  -- Para hotspots
ADD COLUMN grid_y INTEGER;

-- Índices adicionais
CREATE INDEX idx_kills_weapon_class ON sentinel_kills(weapon_class);
CREATE INDEX idx_kills_weapon_category ON sentinel_kills(weapon_category);
CREATE INDEX idx_kills_damage_type ON sentinel_kills(damage_type);
CREATE INDEX idx_kills_killer_npc ON sentinel_kills(killer_is_npc);
CREATE INDEX idx_kills_victim_npc ON sentinel_kills(victim_is_npc);
CREATE INDEX idx_kills_grid ON sentinel_kills(grid_x, grid_y);
```

---

## 📊 Dashboards Sugeridos

### 1. **Kill Feed Live**
- Últimos 50 kills em tempo real
- Filtros: Player kills only, NPC kills, Distance range
- Destaque para long-range kills (>200m)

### 2. **Weapon Meta Analysis**
- Top 10 armas mais usadas
- Kill rate por categoria de arma
- Tendências ao longo do tempo

### 3. **Player Leaderboards**
- Most Kills (24h / 7d / All time)
- Longest Kill
- Best Kill Streak
- Most Revenge Kills

### 4. **PvP Hotspots Map**
- Mapa de calor com áreas de mais PvP
- Filtro por período
- Zoom em áreas específicas

### 5. **Anti-Cheat Dashboard**
- Players com violation_score alto
- Kills suspeitos (distância impossível, etc)
- Padrões anormais

---

## 🚀 Plano de Implementação

### Fase 1: Melhorias Básicas (AGORA)
1. ✅ Separar weapon_class e damage_type
2. ✅ Adicionar weapon_category
3. ✅ Detectar NPCs automaticamente
4. ✅ Calcular grid_x e grid_y

### Fase 2: Análise Avançada (PRÓXIMA)
5. ✅ Implementar kill streaks
6. ✅ Detectar revenge kills
7. ✅ Criar views de estatísticas

### Fase 3: Dashboard (FUTURO)
8. ✅ Kill feed live
9. ✅ Weapon meta analysis
10. ✅ Player leaderboards
11. ✅ PvP hotspots map

---

## 💡 Queries Úteis Imediatas

### Top 10 Armas
```sql
SELECT weapon, COUNT(*) as kills
FROM sentinel_kills
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY weapon
ORDER BY kills DESC
LIMIT 10;
```

### Longest Kills
```sql
SELECT 
    killer_name,
    victim_name,
    weapon,
    distance,
    timestamp
FROM sentinel_kills
WHERE distance > 100
ORDER BY distance DESC
LIMIT 20;
```

### Most Active Players
```sql
SELECT 
    killer_name,
    COUNT(*) as total_kills,
    COUNT(*) FILTER (WHERE distance > 50) as long_range_kills,
    AVG(distance) as avg_distance
FROM sentinel_kills
WHERE timestamp >= NOW() - INTERVAL '24 hours'
  AND killer_id IS NOT NULL
GROUP BY killer_name
ORDER BY total_kills DESC
LIMIT 10;
```

---

## ✅ Resumo Executivo

**Status Atual:** ✅ Sistema funcional capturando dados básicos

**Melhorias Propostas:** 7 melhorias principais
1. Separar weapon class/damage type
2. Categorizar armas
3. Detectar NPCs
4. Kill streaks
5. Revenge kills
6. Hotspots
7. Efficiency metrics

**Impacto Esperado:**
- +200% de insights sobre PvP
- Detecção automática de NPCs
- Análise de meta de armas
- Leaderboards completos
- Mapas de calor de PvP

**Próximo Passo:** Implementar Fase 1 (melhorias básicas)
