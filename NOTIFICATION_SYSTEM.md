# 📨 Sistema de Rastreamento de Notificações WhatsApp

## 📋 Resumo da Implementação

Foi criado um **sistema completo de rastreamento de notificações WhatsApp** para o Sentinel, incluindo:

1. ✅ **Modelo de Banco de Dados** (`SentinelNotificationLog`)
2. ✅ **Serviço de Logging Automático** (integrado ao `notification_service`)
3. ✅ **API REST Completa** (endpoints de consulta e estatísticas)
4. ✅ **Dashboard Administrativo Premium** (interface web moderna)

---

## 🗄️ Banco de Dados

### Tabela: `sentinel_notification_logs`

```sql
CREATE TABLE sentinel_notification_logs (
    id SERIAL PRIMARY KEY,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notification_type VARCHAR(50) NOT NULL,           -- Ex: "raid_alert"
    recipient_phone VARCHAR(20) NOT NULL,             -- Número ou Group JID
    recipient_type VARCHAR(20) NOT NULL,              -- "player", "clan_group", "clan_member"
    recipient_steam_id VARCHAR(50),                   -- Steam ID do destinatário
    recipient_name VARCHAR(255),                      -- Nome do destinatário
    message_content TEXT NOT NULL,                    -- Mensagem completa enviada
    event_context JSONB,                              -- Contexto do evento (raid data, etc)
    status VARCHAR(20) NOT NULL,                      -- "success", "failed", "pending"
    error_message TEXT,                               -- Mensagem de erro (se houver)
    api_response_code INTEGER,                        -- HTTP status code da Evolution API
    api_response_body TEXT,                           -- Response body da API
    evolution_instance VARCHAR(100),                  -- Nome da instância Evolution
    retry_count INTEGER DEFAULT 0                     -- Contador de tentativas
);
```

### Índices Criados
- `idx_notif_sent_at` - Busca por data
- `idx_notif_type` - Filtro por tipo de notificação
- `idx_notif_recipient_phone` - Busca por telefone
- `idx_notif_recipient_steam_id` - Busca por Steam ID
- `idx_notif_status` - Filtro por status

---

## 🔧 Serviço de Notificações

### Arquivo: `app/services/notification_service.py`

**Funcionalidades:**
- ✅ Registra **automaticamente** todas as notificações enviadas
- ✅ Salva **contexto completo** do evento (raid data, localização, etc)
- ✅ Rastreia **sucesso/falha** de cada envio
- ✅ Armazena **mensagens de erro** para debugging
- ✅ Suporta **múltiplos destinatários** (vítima, grupo do clã, membros)

### Exemplo de Log Criado

```python
{
    "notification_type": "raid_alert",
    "recipient_phone": "5577998094395",
    "recipient_type": "player",
    "recipient_steam_id": "76561198254469454",
    "recipient_name": "PlayerName",
    "message_content": "🚨 *ALARME DE BASE* 🚨\n\n⚠️ *PERIGO: TRANCAS VIOLADAS!*...",
    "event_context": {
        "attacker_steam_id": "76561198012345678",
        "attacker_name": "Invasor",
        "target_object": "BasicDoor",
        "lock_type": "Gold Lock",
        "is_success": true,
        "location": {"x": 100.0, "y": 200.0, "z": 300.0}
    },
    "status": "success",
    "api_response_code": 201
}
```

---

## 🌐 API Endpoints

### Base URL: `http://localhost:8000/v2/notifications`

### 1. **GET /notifications**
Lista todas as notificações com filtros opcionais.

**Parâmetros:**
- `skip` (int) - Offset para paginação (padrão: 0)
- `limit` (int) - Limite de resultados (padrão: 50, max: 500)
- `notification_type` (string) - Filtrar por tipo
- `recipient_phone` (string) - Filtrar por telefone
- `recipient_steam_id` (string) - Filtrar por Steam ID
- `status` (string) - Filtrar por status (success/failed/pending)
- `start_date` (datetime) - Data inicial (ISO format)
- `end_date` (datetime) - Data final (ISO format)

**Exemplo de Requisição:**
```bash
curl "http://localhost:8000/v2/notifications?status=failed&limit=10"
```

**Resposta:**
```json
{
    "total": 150,
    "skip": 0,
    "limit": 10,
    "data": [
        {
            "id": 1,
            "sent_at": "2026-01-17T14:30:00",
            "notification_type": "raid_alert",
            "recipient_phone": "5577998094395",
            "recipient_name": "PlayerName",
            "status": "success",
            "message_content": "🚨 ALARME DE BASE...",
            ...
        }
    ]
}
```

---

### 2. **GET /notifications/stats**
Retorna estatísticas agregadas de notificações.

**Parâmetros:**
- `hours` (int) - Período em horas (padrão: 24, max: 168)

**Exemplo de Requisição:**
```bash
curl "http://localhost:8000/v2/notifications/stats?hours=24"
```

**Resposta:**
```json
{
    "period_hours": 24,
    "total_notifications": 150,
    "success_count": 145,
    "failed_count": 5,
    "success_rate": 96.67,
    "by_notification_type": {
        "raid_alert": 150
    },
    "by_recipient_type": {
        "player": 80,
        "clan_group": 30,
        "clan_member": 40
    },
    "recent_failures": [
        {
            "id": 123,
            "sent_at": "2026-01-17T14:25:00",
            "recipient_phone": "5511999999999",
            "recipient_name": "PlayerX",
            "notification_type": "raid_alert",
            "error_message": "Evolution API returned error"
        }
    ]
}
```

---

### 3. **GET /notifications/{notification_id}**
Retorna detalhes completos de uma notificação específica.

**Exemplo de Requisição:**
```bash
curl "http://localhost:8000/v2/notifications/123"
```

---

## 🎨 Dashboard Administrativo

### URL de Acesso
```
http://localhost:8000/admin/notifications_dashboard.html
```

### Funcionalidades

#### 📊 **Estatísticas em Tempo Real**
- Total de notificações enviadas (últimas 24h)
- Taxa de sucesso (%)
- Contador de sucessos
- Contador de falhas

#### 🔍 **Filtros Avançados**
- Status (Sucesso/Falha/Pendente)
- Tipo de Notificação
- Tipo de Destinatário
- Busca por Telefone/Steam ID

#### 📋 **Tabela de Notificações**
- Data/Hora de envio
- Status visual (badges coloridos)
- Tipo de notificação
- Nome do destinatário
- Telefone
- Preview da mensagem
- Mensagem de erro (se houver)

#### ⚡ **Auto-Refresh**
- Atualização automática a cada 30 segundos
- Sem necessidade de recarregar a página

---

## 🚀 Como Usar

### 1. Aplicar Migration
```bash
cd /home/nereu-jr/Área\ de\ trabalho/scum/sentinel-backend
PYTHONPATH=$PWD ./venv/bin/python migrations/apply_notification_logs_migration.py
```

### 2. Reiniciar Backend
```bash
# O backend já está rodando com ./start.sh
# As mudanças serão aplicadas automaticamente se estiver em modo reload
```

### 3. Acessar Dashboard
Abra no navegador:
```
http://localhost:8000/admin/notifications_dashboard.html
```

### 4. Testar Envio de Notificação
```bash
./venv/bin/python simulate_raid.py
```

---

## 📈 Métricas Rastreadas

### Por Notificação
- ✅ Timestamp de envio
- ✅ Tipo de notificação
- ✅ Destinatário (nome, telefone, Steam ID)
- ✅ Conteúdo completo da mensagem
- ✅ Contexto do evento que gerou a notificação
- ✅ Status de envio (sucesso/falha)
- ✅ Código de resposta da API
- ✅ Mensagem de erro detalhada
- ✅ Instância Evolution utilizada
- ✅ Contador de tentativas

### Estatísticas Agregadas
- ✅ Total de notificações por período
- ✅ Taxa de sucesso/falha
- ✅ Distribuição por tipo de notificação
- ✅ Distribuição por tipo de destinatário
- ✅ Últimas falhas (para debugging)

---

## 🎯 Casos de Uso

### 1. Monitorar Saúde do Sistema
```
Acesse /admin/notifications_dashboard.html
Verifique a taxa de sucesso (deve estar > 95%)
```

### 2. Debugar Falhas de Envio
```
Filtre por status="failed"
Analise as mensagens de erro
Verifique se há padrão (mesmo telefone, mesmo horário, etc)
```

### 3. Auditar Notificações Enviadas
```
Busque por Steam ID ou telefone específico
Veja histórico completo de notificações
Verifique conteúdo das mensagens enviadas
```

### 4. Análise de Performance
```
Use o endpoint /stats para ver métricas
Analise distribuição por tipo de destinatário
Identifique horários de pico
```

---

## 🔐 Segurança

⚠️ **IMPORTANTE:** O dashboard atual não possui autenticação!

### Recomendações para Produção:
1. Adicionar autenticação JWT
2. Implementar rate limiting
3. Configurar HTTPS
4. Restringir acesso por IP
5. Adicionar logs de acesso ao dashboard

---

## 🐛 Troubleshooting

### Dashboard não carrega dados
```bash
# Verificar se a API está rodando
curl http://localhost:8000/health

# Verificar endpoint de notificações
curl http://localhost:8000/v2/notifications/stats
```

### Notificações não estão sendo salvas
```bash
# Verificar logs do backend
tail -f logs/sentinel.log | grep "Notification"

# Verificar tabela no banco
psql -U sentinel -d sentinel_db -c "SELECT COUNT(*) FROM sentinel_notification_logs;"
```

### Erro de CORS no dashboard
```
Verifique se o CORS está configurado no main.py
Adicione http://localhost:8000 aos origins permitidos
```

---

## 📝 Próximos Passos (Sugestões)

1. **Retry Automático** - Implementar retry para notificações falhadas
2. **Webhooks** - Notificar sistemas externos sobre falhas
3. **Alertas** - Enviar alerta quando taxa de sucesso < 90%
4. **Exportação** - Permitir exportar relatórios em CSV/PDF
5. **Gráficos** - Adicionar charts de tendência temporal
6. **Templates** - Sistema de templates de mensagens
7. **Agendamento** - Agendar notificações para envio futuro

---

## ✅ Checklist de Implementação

- [x] Modelo de banco de dados criado
- [x] Migration aplicada com sucesso
- [x] Serviço de logging integrado
- [x] Endpoint de listagem implementado
- [x] Endpoint de estatísticas implementado
- [x] Endpoint de detalhes implementado
- [x] Dashboard HTML criado
- [x] Arquivos estáticos configurados no FastAPI
- [x] Auto-refresh implementado
- [x] Filtros funcionais
- [x] Design premium aplicado
- [x] Documentação completa

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs: `tail -f logs/sentinel.log`
2. Teste a API: `curl http://localhost:8000/v2/notifications/stats`
3. Verifique o banco: `psql -U sentinel -d sentinel_db`

---

**Desenvolvido por:** Sentinel AI Team  
**Data:** 2026-01-17  
**Versão:** 1.0.0
