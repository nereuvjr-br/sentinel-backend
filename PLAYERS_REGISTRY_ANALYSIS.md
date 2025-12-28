# Análise: Sistema de Rastreamento de Jogadores e Squads

## 🎯 Problema Identificado

**Desafio:** Jogadores podem mudar de nome a qualquer momento, mas o SteamID permanece constante.

**Necessidades:**
1. Rastrear todos os nomes que um SteamID já usou
2. Identificar o nome atual de cada jogador
3. Associar jogadores a squads/clãs
4. Detectar mudanças de nome suspeitas
5. Histórico completo de aliases

**Limitação dos Logs:**
- Chat com canal "Squad" não identifica QUAL squad
- Não há logs nativos do SCUM com informações de squad/clã
- Squads são organizações informais (Discord, etc)

---

## 💡 Solução Proposta: `sentinel_players_registry`

### Objetivo
Tabela central de jogadores que consolida:
- Histórico de nomes (aliases)
- Nome atual
- Squad/Clã (associação manual ou automática)
- Primeira e última aparição
- Estatísticas básicas

### Estrutura

```sql
CREATE TABLE sentinel_players_registry (
    steam_id VARCHAR(255) PRIMARY KEY,
    
    -- Nome Atual
    current_name VARCHAR(255) NOT NULL,
    previous_names TEXT[],  -- Array de nomes anteriores
    
    -- Squad/Clã
    squad_name VARCHAR(255),
    squad_tag VARCHAR(50),   -- Ex: [TDB], {CLAN}, etc
    squad_joined_at TIMESTAMP,
    
    -- Estatísticas Básicas
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    total_logins INTEGER DEFAULT 0,
    total_playtime_hours DOUBLE PRECISION DEFAULT 0,
    
    -- Flags
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    
    -- Metadados
    notes TEXT,  -- Notas de admin
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Índices
```sql
CREATE INDEX idx_players_current_name ON sentinel_players_registry(current_name);
CREATE INDEX idx_players_squad ON sentinel_players_registry(squad_name);
CREATE INDEX idx_players_last_seen ON sentinel_players_registry(last_seen DESC);
CREATE INDEX idx_players_active ON sentinel_players_registry(is_active);
CREATE INDEX idx_players_squad_tag ON sentinel_players_registry(squad_tag);
```

---

## 📊 Tabela Complementar: `sentinel_name_changes`

### Objetivo
Rastrear cada mudança de nome com timestamp

### Estrutura
```sql
CREATE TABLE sentinel_name_changes (
    id SERIAL PRIMARY KEY,
    steam_id VARCHAR(255) NOT NULL,
    old_name VARCHAR(255),
    new_name VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP NOT NULL,
    detected_in VARCHAR(50),  -- login, chat, kill, etc
    
    FOREIGN KEY (steam_id) REFERENCES sentinel_players_registry(steam_id)
);

CREATE INDEX idx_name_changes_steam_id ON sentinel_name_changes(steam_id);
CREATE INDEX idx_name_changes_date ON sentinel_name_changes(changed_at DESC);
```

---

## 🔄 Processo de Atualização Automática

### 1. Ao Processar Qualquer Log
```python
async def update_player_registry(steam_id: str, player_name: str, event_type: str):
    """
    Atualiza o registro do jogador sempre que ele aparece em qualquer log
    """
    # Buscar registro existente
    player = await get_player(steam_id)
    
    if not player:
        # Novo jogador
        await create_player(
            steam_id=steam_id,
            current_name=player_name,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
    else:
        # Jogador existente
        if player.current_name != player_name:
            # MUDANÇA DE NOME DETECTADA!
            await record_name_change(
                steam_id=steam_id,
                old_name=player.current_name,
                new_name=player_name,
                detected_in=event_type
            )
            
            # Atualizar registro
            await update_player(
                steam_id=steam_id,
                current_name=player_name,
                previous_names=player.previous_names + [player.current_name],
                last_seen=datetime.utcnow()
            )
        else:
            # Apenas atualizar last_seen
            await update_player(
                steam_id=steam_id,
                last_seen=datetime.utcnow()
            )
```

### 2. Detecção Automática de Squad Tags
```python
def extract_squad_tag(player_name: str) -> Optional[str]:
    """
    Extrai tag de squad do nome do jogador
    Padrões comuns: [TAG], {TAG}, TAG|, |TAG|
    """
    import re
    
    patterns = [
        r'\[([A-Z0-9]+)\]',   # [TDB]
        r'\{([A-Z0-9]+)\}',   # {CLAN}
        r'([A-Z0-9]+)\|',     # TAG|
        r'\|([A-Z0-9]+)\|',   # |TAG|
    ]
    
    for pattern in patterns:
        match = re.search(pattern, player_name)
        if match:
            return match.group(1)
    
    return None

# Exemplo de uso
name = "TDB Thui"
tag = extract_squad_tag(name)  # Retorna "TDB" se houver padrão
```

---

## 🎯 Casos de Uso

### 1. Buscar Todos os Nomes de um Jogador
```sql
SELECT 
    steam_id,
    current_name,
    previous_names,
    squad_name
FROM sentinel_players_registry
WHERE steam_id = '76561198066139199';
```

### 2. Histórico de Mudanças de Nome
```sql
SELECT 
    old_name,
    new_name,
    changed_at,
    detected_in
FROM sentinel_name_changes
WHERE steam_id = '76561198066139199'
ORDER BY changed_at DESC;
```

### 3. Listar Todos os Membros de um Squad
```sql
SELECT 
    steam_id,
    current_name,
    squad_tag,
    last_seen,
    is_active
FROM sentinel_players_registry
WHERE squad_name = 'TDB'
  AND is_active = TRUE
ORDER BY last_seen DESC;
```

### 4. Detectar Mudanças de Nome Frequentes (Suspeito)
```sql
SELECT 
    nc.steam_id,
    pr.current_name,
    COUNT(*) as name_changes,
    MAX(nc.changed_at) as last_change
FROM sentinel_name_changes nc
JOIN sentinel_players_registry pr ON nc.steam_id = pr.steam_id
WHERE nc.changed_at >= NOW() - INTERVAL '30 days'
GROUP BY nc.steam_id, pr.current_name
HAVING COUNT(*) > 5
ORDER BY name_changes DESC;
```

### 5. Jogadores Ativos por Squad
```sql
SELECT 
    squad_name,
    COUNT(*) as member_count,
    COUNT(*) FILTER (WHERE last_seen >= NOW() - INTERVAL '7 days') as active_members
FROM sentinel_players_registry
WHERE squad_name IS NOT NULL
GROUP BY squad_name
ORDER BY member_count DESC;
```

---

## 🔧 Integração com Sistema Existente

### Modificar Parsers para Atualizar Registry

Todos os parsers devem chamar `update_player_registry()`:

```python
# Em LoginParserV2
async def save_login(login_data):
    # Salvar login
    await session.add(login_data)
    
    # Atualizar registry
    await update_player_registry(
        steam_id=login_data.steam_id,
        player_name=login_data.player_name,
        event_type='login'
    )

# Em ChatParserV2
async def save_chat(chat_data):
    await session.add(chat_data)
    await update_player_registry(
        steam_id=chat_data.steam_id,
        player_name=chat_data.player_name,
        event_type='chat'
    )

# Em KillParserV2
async def save_kill(kill_data):
    await session.add(kill_data)
    
    # Atualizar killer
    if kill_data.killer_id:
        await update_player_registry(
            steam_id=kill_data.killer_id,
            player_name=kill_data.killer_name,
            event_type='kill'
        )
    
    # Atualizar victim
    await update_player_registry(
        steam_id=kill_data.victim_id,
        player_name=kill_data.victim_name,
        event_type='kill'
    )
```

---

## 🎨 Interface de Administração (Futuro)

### Endpoint para Associar Squad Manualmente
```python
@router.post("/api/players/{steam_id}/squad")
async def assign_squad(
    steam_id: str,
    squad_name: str,
    squad_tag: Optional[str] = None
):
    """
    Permite admin associar jogador a um squad manualmente
    """
    await update_player(
        steam_id=steam_id,
        squad_name=squad_name,
        squad_tag=squad_tag,
        squad_joined_at=datetime.utcnow()
    )
    return {"status": "success"}
```

### Endpoint para Buscar Jogador
```python
@router.get("/api/players/search")
async def search_player(
    query: str  # Pode ser SteamID ou nome
):
    """
    Busca jogador por SteamID ou qualquer nome que já usou
    """
    # Buscar por SteamID
    player = await get_player_by_steam_id(query)
    if player:
        return player
    
    # Buscar por nome atual
    player = await get_player_by_current_name(query)
    if player:
        return player
    
    # Buscar em nomes anteriores
    players = await search_in_previous_names(query)
    return players
```

---

## 📊 Dashboard Sugerido

### Card: "Player Lookup"
- Input: SteamID ou Nome
- Output:
  - Nome atual
  - Todos os nomes anteriores
  - Squad atual
  - Primeira/Última aparição
  - Total de logins
  - Tempo de jogo

### Card: "Squad Members"
- Input: Nome do Squad
- Output:
  - Lista de membros
  - Status (ativo/inativo)
  - Última aparição
  - Link para perfil

### Card: "Recent Name Changes"
- Lista de mudanças de nome nas últimas 24h
- Destaque para mudanças frequentes (>5 em 30 dias)

---

## 🚨 Alertas Automáticos

### Criar em `sentinel_economy_alerts`

1. **frequent_name_changer**
   - Trigger: >5 mudanças de nome em 30 dias
   - Severity: MEDIUM
   - Motivo: Possível tentativa de evasão

2. **impersonation_attempt**
   - Trigger: Nome muito similar a admin/jogador conhecido
   - Severity: HIGH
   - Motivo: Possível tentativa de phishing

---

## 💡 Benefícios

### Para Administração
- ✅ Rastreamento completo de identidade
- ✅ Histórico de aliases
- ✅ Detecção de evasão
- ✅ Organização por squads

### Para Análise
- ✅ Estatísticas por squad
- ✅ Rastreamento de atividade
- ✅ Identificação de jogadores problemáticos
- ✅ Análise de retenção

### Para Comunidade
- ✅ Transparência de identidade
- ✅ Reconhecimento de squads
- ✅ Histórico público (se desejado)

---

## 📝 Resumo Executivo

**Problema:** Jogadores mudam de nome, dificultando rastreamento

**Solução:** 
- Tabela `sentinel_players_registry` (registro central)
- Tabela `sentinel_name_changes` (histórico)
- Atualização automática em todos os parsers
- Detecção automática de squad tags
- Interface para associação manual de squads

**Impacto:**
- 100% de rastreabilidade de identidade
- Histórico completo de aliases
- Organização por squads
- Detecção de comportamento suspeito
