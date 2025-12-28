# Implementação da Tabela sentinel_vehicles

## ✅ Concluído em 2025-12-26

### Arquivos Criados

1. **Model** (`app/models/vehicle_v2.py`)
   - Define a estrutura SQLModel da tabela `sentinel_vehicles`
   - Campos: id, timestamp, vehicle_id, vehicle_class, event_type, owner_id, owner_name, location, processed_at

2. **Parser** (`app/services/parsers_v2/vehicle.py`)
   - Implementa `VehicleParserV2` com regex para extrair eventos de veículos
   - Suporta eventos: Spawned, Destroyed, OwnershipChanged
   - Extrai coordenadas e informações do proprietário

3. **Migração SQL** (`migrations/add_vehicles_table.sql`)
   - Script SQL completo com CREATE TABLE e índices
   - Documentação inline com comentários

4. **Script de Migração** (`migrations/apply_vehicles_migration.py`)
   - Script Python para aplicar a migração usando AsyncSession
   - Executa comandos SQL separadamente para compatibilidade

### Arquivos Modificados

1. **sentinel_v2.py**
   - Adicionado import de `SentinelVehicle` e `VehicleParserV2`
   - Substituído placeholder `lambda x: None` por `VehicleParserV2.parse` (2 locais)
   - Parser agora processa arquivos `log_vehicle_*.log`

2. **DB_SCHEMA_DOCS.md**
   - Atualizado header: 18 → 19 tabelas
   - Adicionada seção "5. Veículos" com documentação completa da nova tabela

3. **app/services/parsers_v2/kill.py**
   - **BUGFIX CRÍTICO**: Adicionados imports faltantes (`Optional`, `SentinelKill`)
   - Corrige erro que impediria salvamento de kills no banco

### Estrutura da Tabela

```sql
CREATE TABLE sentinel_vehicles (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    vehicle_id VARCHAR(255) NOT NULL,      -- ID do veículo no DB do jogo
    vehicle_class VARCHAR(255) NOT NULL,   -- Ex: BPC_Laika
    event_type VARCHAR(100) NOT NULL,      -- Spawned, Destroyed, etc
    owner_id VARCHAR(255),                 -- SteamID do owner
    owner_name VARCHAR(255),
    location JSONB,                        -- {x, y, z}
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Índices criados:**
- `idx_vehicles_timestamp`
- `idx_vehicles_vehicle_id`
- `idx_vehicles_vehicle_class`
- `idx_vehicles_owner_id`
- `idx_vehicles_event_type`

### Benefícios

1. **Investigação de Roubos**: Rastreamento completo do ciclo de vida de veículos
2. **Monitoramento de Performance**: Identificação de vehicle hoarding
3. **Auditoria de Bugs**: Detecção de veículos em coordenadas inválidas
4. **Administração Proativa**: Visibilidade sobre spawn/despawn patterns

### Status

✅ **Migração aplicada com sucesso no banco `sentinel_dev`**
✅ **Parser integrado ao daemon `sentinel_v2.py`**
✅ **Documentação atualizada**
✅ **Bugfix crítico aplicado em kill.py**

### Próximos Passos (Opcional)

- [ ] Criar endpoint API para consultar eventos de veículos
- [ ] Adicionar dashboard no frontend para visualização
- [ ] Implementar alertas para vehicle hoarding
- [ ] Criar relatório de veículos perdidos/destruídos
