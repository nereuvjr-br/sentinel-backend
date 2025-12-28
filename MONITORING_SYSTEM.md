# Sistema de Monitoramento Completo - Sentinel V2

## 📋 Visão Geral

O Sistema de Monitoramento do Sentinel V2 foi projetado para garantir que todos os parsers estão funcionando corretamente e que o banco de dados está sendo alimentado adequadamente. Ele fornece visibilidade completa sobre:

- **Performance de Parsers**: Rastreamento detalhado de cada parser
- **Saúde do Banco de Dados**: Snapshots periódicos do estado das tabelas
- **Logs de Ingestão**: Histórico completo de processamento de arquivos
- **Sistema de Alertas**: Detecção automática de anomalias

---

## 🏗️ Arquitetura

### Componentes Principais

1. **Models** (`app/models/monitoring_v2.py`)
   - `SentinelParserMetrics`: Métricas de performance de cada parser
   - `SentinelDatabaseHealth`: Snapshots de saúde do banco
   - `SentinelIngestionLog`: Logs detalhados de ingestão
   - `SentinelSystemAlert`: Sistema de alertas

2. **Service** (`app/services/monitoring_service.py`)
   - `MonitoringService`: Lógica centralizada de monitoramento
   - Captura de métricas
   - Geração de snapshots
   - Criação automática de alertas

3. **API** (`app/api/v2/endpoints/monitoring.py`)
   - Endpoints REST para acesso às métricas
   - Gerenciamento de alertas
   - Relatórios de saúde

4. **Integração no Daemon** (`sentinel_v2.py`)
   - Rastreamento automático durante ingestão
   - Health checks periódicos (5 minutos)
   - Registro de métricas em tempo real

---

## 📊 Tabelas do Banco de Dados

### 1. `sentinel_parser_metrics`

Rastreia a performance de cada parser individualmente.

**Campos Principais:**
- `parser_name`: Nome do parser (Admin, Chat, Economy, etc.)
- `total_lines_processed`: Total de linhas processadas
- `total_lines_success`: Linhas parseadas com sucesso
- `total_lines_failed`: Linhas que falharam
- `success_rate`: Taxa de sucesso (%)
- `is_healthy`: Status de saúde (threshold: 95%)
- `avg_parse_time_ms`: Tempo médio de parse por linha
- `last_error`: Último erro registrado

**Uso:**
```sql
SELECT parser_name, success_rate, is_healthy, total_lines_processed
FROM sentinel_parser_metrics
ORDER BY success_rate ASC;
```

### 2. `sentinel_database_health`

Snapshots periódicos do estado de todas as tabelas.

**Campos Principais:**
- Contadores para cada tabela (`count_kills`, `count_economy_trades`, etc.)
- Taxas de crescimento (`growth_rate_kills`, `growth_rate_trades`, etc.)
- `is_healthy`: Status geral
- `health_issues`: Array JSON com problemas detectados
- `snapshot_at`: Timestamp do snapshot

**Uso:**
```sql
SELECT snapshot_at, is_healthy, 
       count_kills, count_economy_trades, 
       growth_rate_kills
FROM sentinel_database_health
ORDER BY snapshot_at DESC
LIMIT 10;
```

### 3. `sentinel_ingestion_logs`

Histórico completo de cada ciclo de ingestão.

**Campos Principais:**
- `filename`: Nome do arquivo processado
- `log_type`: Tipo de log (Admin, Economy, etc.)
- `lines_processed`: Linhas processadas
- `lines_success` / `lines_failed`: Resultado
- `processing_time_ms`: Tempo de processamento
- `throughput_lines_per_sec`: Throughput (linhas/segundo)
- `status`: success, partial, failed
- `offset_start` / `offset_end`: Posição no arquivo

**Uso:**
```sql
SELECT filename, log_type, lines_processed, 
       throughput_lines_per_sec, status
FROM sentinel_ingestion_logs
WHERE status = 'failed'
ORDER BY started_at DESC;
```

### 4. `sentinel_system_alerts`

Sistema de alertas para anomalias detectadas.

**Campos Principais:**
- `alert_type`: Tipo de alerta (parser_degraded, db_anomaly, etc.)
- `severity`: low, medium, high, critical
- `component`: Componente afetado
- `title` / `description`: Detalhes do alerta
- `evidence`: JSON com evidências
- `status`: open, acknowledged, resolved, false_positive

**Uso:**
```sql
SELECT alert_type, severity, component, title, detected_at
FROM sentinel_system_alerts
WHERE status = 'open'
ORDER BY severity DESC, detected_at DESC;
```

---

## 🔌 API Endpoints

### Base URL: `/api/v2/monitoring`

### 1. **GET** `/health`
Relatório completo de saúde do sistema.

**Resposta:**
```json
{
  "timestamp": "2025-12-26T23:00:00",
  "overall_health": "healthy",
  "database_snapshot": {
    "total_records": 150000,
    "growth_rates": {
      "kills_per_min": 12.5,
      "trades_per_min": 8.3,
      "logins_per_min": 2.1
    },
    "issues": []
  },
  "parsers": [...],
  "alerts": [...],
  "recent_ingestions": [...]
}
```

### 2. **GET** `/parsers`
Métricas detalhadas de todos os parsers.

### 3. **GET** `/database/snapshots?limit=10`
Últimos snapshots de saúde do banco.

### 4. **GET** `/ingestion/logs?limit=50&log_type=Economy&status=failed`
Logs de ingestão com filtros opcionais.

### 5. **GET** `/alerts?status=open&severity=high`
Alertas do sistema com filtros.

### 6. **POST** `/alerts/{alert_id}/acknowledge`
Reconhecer um alerta.

**Body:**
```json
{
  "acknowledged_by": "admin_name"
}
```

### 7. **POST** `/alerts/{alert_id}/resolve`
Resolver um alerta.

**Body:**
```json
{
  "resolved_by": "admin_name",
  "resolution_notes": "Problema corrigido reiniciando o parser"
}
```

### 8. **GET** `/stats/summary`
Resumo executivo do monitoramento.

**Resposta:**
```json
{
  "overall_status": "healthy",
  "database_health": {
    "is_healthy": true,
    "last_check": "2025-12-26T23:00:00",
    "issues_count": 0
  },
  "parsers": {
    "total": 10,
    "unhealthy": 0,
    "unhealthy_list": []
  },
  "alerts": {
    "total_open": 2,
    "by_severity": {
      "critical": 0,
      "high": 1,
      "medium": 1,
      "low": 0
    }
  },
  "ingestion": {
    "failed_last_hour": 0
  }
}
```

---

## 🚀 Como Usar

### 1. Executar Migração

```bash
cd sentinel-backend
python migrations/add_monitoring_tables.py
```

### 2. Iniciar o Daemon

O monitoramento é automático quando o daemon está rodando:

```bash
python sentinel_v2.py
```

**O que acontece:**
- Cada arquivo processado gera métricas de parser
- Cada ciclo de ingestão é registrado
- A cada 5 minutos, um snapshot de saúde é capturado
- Alertas são criados automaticamente quando problemas são detectados

### 3. Acessar Métricas via API

```bash
# Health check geral
curl http://localhost:8000/api/v2/monitoring/health

# Ver parsers
curl http://localhost:8000/api/v2/monitoring/parsers

# Ver alertas abertos
curl http://localhost:8000/api/v2/monitoring/alerts?status=open

# Resumo executivo
curl http://localhost:8000/api/v2/monitoring/stats/summary
```

---

## 📈 Métricas Rastreadas

### Por Parser:
- Total de linhas processadas
- Taxa de sucesso (%)
- Tempo médio de parse (ms)
- Throughput (linhas/segundo)
- Contagem de erros
- Status de saúde

### Por Banco de Dados:
- Contagem de registros em todas as tabelas
- Taxa de crescimento (registros/minuto)
- Detecção de estagnação (sem crescimento)
- Detecção de logs não parseados excessivos

### Por Ingestão:
- Bytes processados
- Linhas processadas/sucesso/falha
- Tempo de processamento
- Throughput
- Status (success/partial/failed)

---

## 🚨 Sistema de Alertas

### Tipos de Alertas:

1. **`parser_degraded`**
   - Disparado quando taxa de sucesso < 95%
   - Severidade: high (< 80%) ou medium (80-95%)

2. **`high_unparsed_count`**
   - Disparado quando > 1000 logs não parseados
   - Severidade: medium

3. **`no_growth_detected`**
   - Disparado quando não há crescimento por > 10 minutos
   - Severidade: high

4. **`ingestion_stalled`**
   - Disparado quando ingestão para completamente
   - Severidade: critical

### Workflow de Alertas:

1. **Detecção Automática**: Sistema detecta anomalia
2. **Criação**: Alerta é criado com status `open`
3. **Notificação**: Log de warning é gerado
4. **Reconhecimento**: Admin marca como `acknowledged`
5. **Resolução**: Admin resolve e adiciona notas
6. **Histórico**: Alerta permanece no banco para auditoria

---

## 🔍 Queries Úteis

### Parsers com Problemas
```sql
SELECT parser_name, success_rate, total_lines_failed, last_error
FROM sentinel_parser_metrics
WHERE is_healthy = FALSE
ORDER BY success_rate ASC;
```

### Crescimento nas Últimas 24h
```sql
SELECT 
    snapshot_at,
    count_kills,
    count_economy_trades,
    growth_rate_kills,
    growth_rate_trades
FROM sentinel_database_health
WHERE snapshot_at >= NOW() - INTERVAL '24 hours'
ORDER BY snapshot_at DESC;
```

### Ingestões Falhadas Hoje
```sql
SELECT filename, log_type, error_message, started_at
FROM sentinel_ingestion_logs
WHERE status = 'failed'
  AND started_at >= CURRENT_DATE
ORDER BY started_at DESC;
```

### Alertas Críticos Abertos
```sql
SELECT alert_type, component, title, description, detected_at
FROM sentinel_system_alerts
WHERE status = 'open'
  AND severity IN ('critical', 'high')
ORDER BY detected_at DESC;
```

---

## 📝 Logs do Sistema

O daemon gera logs detalhados:

```
🚀 Sentinel V2 (Tailing Mode) Iniciado. Monitorando 192.168.1.100...
🏥 Health Check Task iniciada (intervalo: 5 minutos)
📂 Tailing economy.log (Size: 1048576 > Offset: 524288)
📊 Ingestão: economy.log | 1250 linhas | 625.5 linhas/s | Status: success
✅ Atualizado economy.log: +1250 eventos.
📸 Snapshot de Saúde: 0 problemas detectados
✅ Sistema saudável
```

---

## 🛠️ Manutenção

### Limpeza de Dados Antigos

Para evitar crescimento excessivo, considere limpar dados antigos:

```sql
-- Manter apenas últimos 30 dias de logs de ingestão
DELETE FROM sentinel_ingestion_logs
WHERE started_at < NOW() - INTERVAL '30 days';

-- Manter apenas últimos 90 dias de snapshots
DELETE FROM sentinel_database_health
WHERE snapshot_at < NOW() - INTERVAL '90 days';

-- Manter alertas resolvidos por 180 dias
DELETE FROM sentinel_system_alerts
WHERE status = 'resolved'
  AND resolved_at < NOW() - INTERVAL '180 days';
```

### Ajuste de Thresholds

Edite `app/services/monitoring_service.py` para ajustar:

```python
# Taxa de sucesso mínima para parser saudável
metric.is_healthy = metric.success_rate >= 95.0  # Altere aqui

# Limite de logs não parseados
if snapshot.count_unparsed_logs > 1000:  # Altere aqui
```

---

## ✅ Checklist de Implementação

- [x] Modelos de dados criados
- [x] Serviço de monitoramento implementado
- [x] Integração no daemon principal
- [x] Health checks periódicos
- [x] API endpoints completos
- [x] Sistema de alertas automáticos
- [x] Migração de banco de dados
- [x] Documentação completa

---

## 🎯 Próximos Passos

1. **Frontend Dashboard**: Criar interface visual para monitoramento
2. **Notificações**: Integrar com Discord/Slack para alertas
3. **Métricas Avançadas**: Adicionar análise de tendências
4. **Auto-Recovery**: Implementar recuperação automática de falhas
5. **Performance Profiling**: Identificar gargalos de performance

---

## 📞 Suporte

Para problemas ou dúvidas sobre o sistema de monitoramento:

1. Verifique os logs do daemon
2. Consulte `/api/v2/monitoring/health`
3. Revise alertas em `/api/v2/monitoring/alerts`
4. Analise métricas de parsers específicos
