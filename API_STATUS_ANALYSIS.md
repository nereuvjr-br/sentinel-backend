# 📊 Análise: Estado Atual das APIs de Economy e Killfeed

## ✅ O QUE JÁ EXISTE

### Economy API (`/api/v2/economy/`)
**Endpoints Implementados:**
1. ✅ `GET /trades/` - Lista transações (compra/venda)
2. ✅ `GET /balances/` - Lista snapshots de saldo

**Recursos:**
- Paginação (limit/offset)
- Busca por nome, SteamID, item, trader
- Filtro por tipo de transação
- Filtro por wipe date

### Kills API (`/api/v2/kills/`)
**Endpoints Implementados:**
1. ✅ `GET /` - Lista kills

**Recursos:**
- Paginação (limit/offset)
- Busca por nome, SteamID, arma
- Filtro por killer_id, victim_id
- Filtro por weapon, is_event
- Filtro por data (date_from, date_to)

---

## ❌ O QUE ESTÁ FALTANDO

### Economy API - Endpoints Ausentes

#### 1. **Novas Tabelas Não Expostas**
- ❌ `/wallets/` - sentinel_player_wallets
- ❌ `/items/` - sentinel_item_economy
- ❌ `/alerts/` - sentinel_economy_alerts
- ❌ `/traders/` - sentinel_trader_inventory
- ❌ `/accounts/` - sentinel_account_registry
- ❌ `/admin-actions/` - sentinel_admin_economy_actions

#### 2. **Endpoints de Análise**
- ❌ `/stats/top-players` - Top jogadores mais ricos
- ❌ `/stats/item-meta` - Itens mais negociados
- ❌ `/stats/inflation` - Análise de inflação
- ❌ `/alerts/active` - Alertas ativos

### Kills API - Endpoints Ausentes

#### 1. **Novos Campos Não Utilizados**
- ❌ Filtro por `weapon_category`
- ❌ Filtro por `damage_type`
- ❌ Filtro por `killer_is_npc` / `victim_is_npc`
- ❌ Filtro por `grid_x` / `grid_y`

#### 2. **Views Não Expostas**
- ❌ `/stats/players` - sentinel_player_kill_stats
- ❌ `/stats/weapons` - sentinel_weapon_meta
- ❌ `/stats/hotspots` - sentinel_pvp_hotspots
- ❌ `/stats/npcs` - sentinel_npc_kill_stats

#### 3. **Endpoints de Análise**
- ❌ `/leaderboard` - Top killers
- ❌ `/weapon-meta` - Análise de armas
- ❌ `/hotspots` - Áreas quentes
- ❌ `/player/{steam_id}/stats` - Estatísticas individuais

---

## 🚀 PLANO DE IMPLEMENTAÇÃO

### Fase 1: Economy API - Novas Tabelas (PRIORITÁRIO)

#### Arquivo: `app/api/v2/endpoints/economy_analytics.py`

```python
from fastapi import APIRouter, Query, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.economy_analytics_v2 import (
    SentinelPlayerWallet,
    SentinelItemEconomy,
    SentinelEconomyAlert,
    SentinelTraderInventory,
    SentinelAccountRegistry
)

router = APIRouter()

# 1. Player Wallets
@router.get("/wallets/")
async def get_player_wallets(...)

@router.get("/wallets/top")
async def get_top_players(...)

@router.get("/wallets/{steam_id}")
async def get_player_wallet(...)

# 2. Item Economy
@router.get("/items/")
async def get_item_economy(...)

@router.get("/items/trending")
async def get_trending_items(...)

# 3. Economy Alerts
@router.get("/alerts/")
async def get_economy_alerts(...)

@router.get("/alerts/active")
async def get_active_alerts(...)

# 4. Trader Inventory
@router.get("/traders/")
async def get_trader_inventory(...)

@router.get("/traders/{trader_name}")
async def get_trader_details(...)

# 5. Account Registry
@router.get("/accounts/")
async def get_accounts(...)

@router.get("/accounts/{account_number}")
async def get_account_details(...)
```

### Fase 2: Kills API - Melhorias (PRIORITÁRIO)

#### Arquivo: `app/api/v2/endpoints/kills_analytics.py`

```python
from fastapi import APIRouter, Query, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session

router = APIRouter()

# 1. Player Stats (View)
@router.get("/stats/players")
async def get_player_stats(...)

@router.get("/stats/players/{steam_id}")
async def get_player_stats_detail(...)

# 2. Weapon Meta (View)
@router.get("/stats/weapons")
async def get_weapon_meta(...)

@router.get("/stats/weapons/{category}")
async def get_weapon_category_stats(...)

# 3. PvP Hotspots (View)
@router.get("/stats/hotspots")
async def get_pvp_hotspots(...)

# 4. NPC Stats (View)
@router.get("/stats/npcs")
async def get_npc_stats(...)

# 5. Leaderboards
@router.get("/leaderboard/pvp")
async def get_pvp_leaderboard(...)

@router.get("/leaderboard/distance")
async def get_distance_leaderboard(...)
```

### Fase 3: Atualizar Endpoint Existente de Kills

#### Adicionar novos filtros:
```python
@router.get("/", response_model=List[SentinelKill])
async def get_kill_logs(
    # ... parâmetros existentes ...
    weapon_category: Optional[str] = None,  # NEW
    damage_type: Optional[str] = None,      # NEW
    killer_is_npc: Optional[bool] = None,   # NEW
    victim_is_npc: Optional[bool] = None,   # NEW
    grid_x: Optional[int] = None,           # NEW
    grid_y: Optional[int] = None,           # NEW
):
```

---

## 📝 RESUMO EXECUTIVO

### Economy API
**Status:** ⚠️ **PARCIALMENTE IMPLEMENTADA**
- ✅ Endpoints básicos (trades, balances)
- ❌ 6 novas tabelas não expostas
- ❌ Endpoints de análise ausentes

### Kills API
**Status:** ⚠️ **PARCIALMENTE IMPLEMENTADA**
- ✅ Endpoint básico de listagem
- ❌ Novos campos não utilizados
- ❌ 4 views não expostas
- ❌ Endpoints de análise ausentes

### Ação Necessária
**IMPLEMENTAR:**
1. Economy Analytics API (10+ endpoints)
2. Kills Analytics API (10+ endpoints)
3. Atualizar endpoints existentes com novos filtros

**Impacto:**
- Economy: +1000% de funcionalidades
- Kills: +500% de funcionalidades
- Total: 20+ novos endpoints
