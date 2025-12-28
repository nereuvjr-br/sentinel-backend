# Documentação Completa do Schema de Banco de Dados - Sentinel V2

Este documento descreve a estrutura **exata e completa** das 24 tabelas do banco de dados `sentinel_dev`, conforme verificado via introspecção em `2025-12-26`.

---

## 1. Tabelas Principais (Core)

### `sentinel_admin_commands`
Registra todos os comandos de administração.
- `id` (INTEGER): Chave Primária.
- `timestamp` (TIMESTAMP): Data/Hora UTC.
- `admin_steam_id` (VARCHAR): SteamID64 do admin.
- `admin_name` (VARCHAR): Nome do admin.
- `admin_game_id` (VARCHAR): ID de jogo (ex: 123).
- `raw_command` (VARCHAR): O comando digitado.
- `command_type` (VARCHAR): Tipo normalizado (Teleport, SpawnItem, etc).
- `target_steam_id` (VARCHAR): SteamID do alvo (se houver).
- `target_name` (VARCHAR): Nome do alvo.
- `item_class` (VARCHAR): Classe do item spawnado (se spawn).
- `item_count` (INTEGER): Quantidade.
- `item_args` (VARCHAR): Argumentos extras.
- `location` (JSON): `{x, y, z}` do admin.
- `is_automated` (BOOLEAN): Se foi bot/rcon.
- `processed_at` (TIMESTAMP): Data de processamento.

### `sentinel_chat_messages`
Histórico de conversas.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `player_name` (VARCHAR)
- `game_id` (INTEGER)
- `channel` (VARCHAR): Global, Local, Squad, Admin.
- `message` (VARCHAR)
- `is_automated` (BOOLEAN)
- `processed_at` (TIMESTAMP)

### `sentinel_logins`
Sessões de jogadores.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `player_name` (VARCHAR)
- `game_id` (INTEGER)
- `ip_address` (VARCHAR)
- `action` (VARCHAR): Login ou Logout.
- `login_type` (VARCHAR): Regular, Drone, etc.
- `location` (JSON): Coordenadas.
- `processed_at` (TIMESTAMP)

### `sentinel_kills`
Killfeed completo (PvP/PvE).
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `killer_id` (VARCHAR): SteamID do matador (ou None).
- `killer_name` (VARCHAR)
- `killer_loc_server` (JSON): Posição server-side.
- `killer_loc_client` (JSON): Posição client-side.
- `killer_immortal` (BOOLEAN)
- `victim_id` (VARCHAR)
- `victim_name` (VARCHAR)
- `victim_loc` (JSON)
- `weapon` (VARCHAR): Causa da morte.
- `distance` (DOUBLE PRECISION)
- `is_event` (BOOLEAN): Morte em evento.
- `time_of_day` (VARCHAR)
- `violation_score` (DOUBLE PRECISION): Anti-Cheat metric.
- `processed_at` (TIMESTAMP)

---

## 2. Economia e Comércio

### `sentinel_economy_trades`
Compras e Vendas em NPCs.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `player_name` (VARCHAR)
- `account_number` (VARCHAR)
- `trade_type` (VARCHAR): "Purchase" ou "Sell".
- `item_class` (VARCHAR)
- `item_count` (INTEGER)
- `item_health` (DOUBLE PRECISION): Durabilidade (0-1).
- `item_uses` (INTEGER): Cargas/Munição.
- `total_price` (DOUBLE PRECISION)
- `trader_name` (VARCHAR)
- `is_mechanic_service` (BOOLEAN)
- `users_online` (INTEGER): Contexto do mercado dinâmico.
- `store_stock_before` (INTEGER)
- `store_stock_after` (INTEGER)
- `pos_x` (DOUBLE PRECISION)
- `pos_y` (DOUBLE PRECISION)
- `pos_z` (DOUBLE PRECISION)

### `sentinel_economy_balances`
Snapshots de saldo.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `player_name` (VARCHAR)
- `account_number` (VARCHAR)
- `trigger_event` (VARCHAR)
- `trader_name` (VARCHAR)
- `cash` (DOUBLE PRECISION)
- `bank` (DOUBLE PRECISION)
- `gold` (DOUBLE PRECISION)
- `trader_funds` (DOUBLE PRECISION)
- `pos_x` (DOUBLE PRECISION)
- `pos_y` (DOUBLE PRECISION)
- `pos_z` (DOUBLE PRECISION)
- `processed_at` (TIMESTAMP)

### `sentinel_bank_transactions`
Movimentações financeiras.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `player_name` (VARCHAR)
- `account_number` (VARCHAR)
- `transaction_type` (VARCHAR): deposit, withdraw, transfer.
- `gross_amount` (DOUBLE PRECISION): Valor bruto.
- `net_amount` (DOUBLE PRECISION): Valor líquido.
- `fee` (DOUBLE PRECISION): Taxa cobrada.
- `target_account` (VARCHAR)
- `target_name` (VARCHAR)
- `target_steam_id` (VARCHAR)
- `pos_x` (DOUBLE PRECISION)
- `pos_y` (DOUBLE PRECISION)
- `pos_z` (DOUBLE PRECISION)

### `sentinel_bank_cards`
Cartões de crédito.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `player_name` (VARCHAR)
- `account_number` (VARCHAR)
- `action` (VARCHAR): purchased, destroyed.
- `card_type` (VARCHAR)
- `free_renewal` (BOOLEAN)
- `new_balance` (DOUBLE PRECISION)
- `destroyed_account` (VARCHAR)
- `pos_x` (DOUBLE PRECISION)
- `pos_y` (DOUBLE PRECISION)
- `pos_z` (DOUBLE PRECISION)

### `sentinel_mechanic_services`
Serviços em veículos.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `player_name` (VARCHAR)
- `service_type` (VARCHAR): Repair, Install, etc.
- `item_class` (VARCHAR)
- `price` (DOUBLE PRECISION)
- `trader_name` (VARCHAR)
- `pos_x` (DOUBLE PRECISION)
- `pos_y` (DOUBLE PRECISION)
- `pos_z` (DOUBLE PRECISION)

---

## 3. Gameplay e Eventos

### `sentinel_gameplay_raids`
Minigames de Lockpicking.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `attacker_steam_id` (VARCHAR)
- `attacker_name` (VARCHAR)
- `target_owner_steam_id` (VARCHAR)
- `target_owner_name` (VARCHAR)
- `minigame_class` (VARCHAR)
- `target_object` (VARCHAR)
- `lock_type` (VARCHAR)
- `is_success` (BOOLEAN)
- `failed_attempts` (INTEGER)
- `elapsed_time` (DOUBLE PRECISION)
- `location` (JSON)
- `processed_at` (TIMESTAMP)

### `sentinel_gameplay_explosives`
Uso de C4/Minas.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `player_name` (VARCHAR)
- `action` (VARCHAR): Armed, Exploded.
- `item_class` (VARCHAR)
- `location` (JSON)
- `processed_at` (TIMESTAMP)

### `sentinel_gameplay_bunkers`
Ativação de Killbox.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `bunker_name` (VARCHAR)
- `action` (VARCHAR)
- `location` (JSON)
- `processed_at` (TIMESTAMP)

### `sentinel_gameplay_crafting`
Criação de itens.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `crafter_steam_id` (VARCHAR)
- `crafter_name` (VARCHAR)
- `item_class` (VARCHAR)
- `count` (INTEGER)
- `location` (JSON)
- `processed_at` (TIMESTAMP)

### `sentinel_chest_events`
Claim de baús.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `action` (VARCHAR)
- `entity_id` (VARCHAR)
- `location` (JSON)
- `processed_at` (TIMESTAMP)

### `sentinel_fame_events`
Pontos de Fama.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `player_name` (VARCHAR)
- `amount` (DOUBLE PRECISION)
- `reason` (VARCHAR)
- `processed_at` (TIMESTAMP)

---

## 4. Segurança e Sistema

### `sentinel_violations`
Logs de Anti-Cheat.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `steam_id` (VARCHAR)
- `player_name` (VARCHAR)
- `violation_class` (VARCHAR): ex: AmmoCountMismatch.
- `description` (VARCHAR)
- `weapon` (VARCHAR): Arma usada (se cheat de munição).
- `location` (JSON): Onde ocorreu.
- `suspicious_count` (INTEGER): Acumulado de suspeitas.
- `ban_count` (INTEGER)
- `processed_at` (TIMESTAMP)

### `sentinel_processed_files`
Controle de ingestão.
- `filename` (VARCHAR)
- `log_type` (VARCHAR)
- `processed_at` (TIMESTAMP)
- `last_modified` (TIMESTAMP)
- `processed_bytes` (BIGINT)
- `lines_processed` (INTEGER)
- `status` (VARCHAR)

### `sentinel_unparsed_logs`
Logs com erro de parse.
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `log_type` (VARCHAR)
- `filename` (VARCHAR)
- `raw_line` (TEXT)
- `attempted_parsers` (VARCHAR)
- `error_message` (VARCHAR)

---

## 5. Veículos

### `sentinel_vehicles`
Registra lifecycle de veículos (spawn, destroy, claim).
- `id` (INTEGER)
- `timestamp` (TIMESTAMP)
- `vehicle_id` (VARCHAR): ID do veículo no DB do jogo.
- `vehicle_class` (VARCHAR): Ex: BPC_Laika.
- `event_type` (VARCHAR): Spawned, Destroyed, etc.
- `owner_id` (VARCHAR): SteamID do owner (se houver).
- `owner_name` (VARCHAR)
- `location` (JSON): Coordenadas.
- `processed_at` (TIMESTAMP)

---

## 6. Análise Econômica (Economic Analytics)

### `sentinel_player_wallets`
Consolidação do estado atual da carteira de cada jogador.
- `steam_id` (VARCHAR): PK - SteamID do jogador.
- `player_name` (VARCHAR): Nome do jogador.
- `cash` (DOUBLE PRECISION): Dinheiro em mãos.
- `bank` (DOUBLE PRECISION): Saldo bancário.
- `gold` (DOUBLE PRECISION): Ouro.
- `total_earned` (DOUBLE PRECISION): Total ganho (lifetime).
- `total_spent` (DOUBLE PRECISION): Total gasto (lifetime).
- `primary_account_number` (VARCHAR): Conta bancária principal.
- `account_count` (INTEGER): Número de contas.
- `first_seen` (TIMESTAMP): Primeira aparição.
- `last_transaction` (TIMESTAMP): Última transação.
- `updated_at` (TIMESTAMP): Última atualização.

### `sentinel_item_economy`
Análise agregada da economia de cada item.
- `id` (INTEGER): PK.
- `item_class` (VARCHAR): Classe do item.
- `total_purchases` (BIGINT): Total de compras.
- `total_purchase_value` (DOUBLE PRECISION): Valor total em compras.
- `avg_purchase_price` (DOUBLE PRECISION): Preço médio de compra.
- `total_sales` (BIGINT): Total de vendas.
- `total_sale_value` (DOUBLE PRECISION): Valor total em vendas.
- `avg_sale_price` (DOUBLE PRECISION): Preço médio de venda.
- `avg_sale_health` (DOUBLE PRECISION): Durabilidade média em vendas.
- `avg_sale_uses` (INTEGER): Munição/cargas médias.
- `price_trend` (VARCHAR): Tendência (rising, falling, stable).
- `demand_level` (VARCHAR): Demanda (high, medium, low).
- `most_sold_trader` (VARCHAR): Trader que mais vende.
- `most_bought_trader` (VARCHAR): Trader que mais compra.
- `period_start` (TIMESTAMP): Início do período.
- `period_end` (TIMESTAMP): Fim do período.
- `updated_at` (TIMESTAMP): Última atualização.

### `sentinel_economy_alerts`
Sistema de alertas automáticos para anomalias econômicas.
- `id` (INTEGER): PK.
- `alert_type` (VARCHAR): Tipo (dupe_detected, inflation_spike, etc).
- `severity` (VARCHAR): Severidade (low, medium, high, critical).
- `steam_id` (VARCHAR): SteamID relacionado.
- `player_name` (VARCHAR): Nome do jogador.
- `trader_name` (VARCHAR): Trader relacionado.
- `item_class` (VARCHAR): Item relacionado.
- `account_number` (VARCHAR): Conta relacionada.
- `description` (TEXT): Descrição do alerta.
- `evidence` (JSONB): Evidências (JSON).
- `status` (VARCHAR): Status (open, investigating, resolved, false_positive).
- `assigned_admin` (VARCHAR): Admin responsável.
- `detected_at` (TIMESTAMP): Data de detecção.
- `resolved_at` (TIMESTAMP): Data de resolução.
- `created_at` (TIMESTAMP): Data de criação.

### `sentinel_trader_inventory`
Rastreamento de estoque e fundos de traders.
- `id` (INTEGER): PK.
- `trader_name` (VARCHAR): Nome do trader.
- `funds` (DOUBLE PRECISION): Fundos disponíveis.
- `item_class` (VARCHAR): Classe do item.
- `stock_quantity` (INTEGER): Quantidade em estoque.
- `users_online` (INTEGER): Usuários online (contexto).
- `snapshot_time` (TIMESTAMP): Momento do snapshot.

### `sentinel_account_registry`
Registro de todas as contas bancárias.
- `account_number` (VARCHAR): PK - Número da conta.
- `current_owner_steam_id` (VARCHAR): SteamID do proprietário atual.
- `current_owner_name` (VARCHAR): Nome do proprietário.
- `created_at` (TIMESTAMP): Data de criação.
- `last_transaction` (TIMESTAMP): Última transação.
- `total_deposits` (DOUBLE PRECISION): Total depositado.
- `total_withdrawals` (DOUBLE PRECISION): Total sacado.
- `total_transfers_in` (DOUBLE PRECISION): Total recebido em transferências.
- `total_transfers_out` (DOUBLE PRECISION): Total enviado em transferências.
- `is_active` (BOOLEAN): Conta ativa.
- `has_card` (BOOLEAN): Possui cartão.
- `card_type` (VARCHAR): Tipo de cartão.
- `updated_at` (TIMESTAMP): Última atualização.

