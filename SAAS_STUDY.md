# 🚀 Estudo de Transformação SaaS - Sentinel Platform

## 1. Resumo Executivo
Atualmente, o **Sentinel** opera como uma solução **Self-Hosted/Single-Tenant**: uma instância do backend conecta-se a um único servidor de jogo via SFTP. Para transformar o Sentinel em um produto **SaaS (Software as a Service)** comercializável, precisamos evoluir a arquitetura para suportar múltiplos clientes (Donos de Servidores de SCUM), onde cada cliente pode gerenciar múltiplos servidores de jogo, tudo em uma infraestrutura compartilhada e escalável.

---

## 2. Mudanças Arquiteturais Fundamentais

### 2.1. De "Single Config" para "Database Driven"
*   **Atual:** As credenciais SFTP (`SFTP_HOST`, `SFTP_USER` etc.) estão hardcoded no `.env`.
*   **Novo:** As credenciais devem residir em uma tabela `servers` no banco de dados. O Backend não lerá mais o `.env` para conectar, mas sim iterará sobre as linhas ativas desta tabela.

### 2.2. Multi-Tenancy (Isolamento de Dados)
Todos os dados ingeridos devem pertencer a um Servidor específico.
*   **Ação:** Adicionar uma coluna `server_id` (Foreign Key) em **TODAS** as 24 tabelas de logs (`sentinel_kills`, `sentinel_chat`, etc.).
*   **Ação:** Atualizar todas as Composite Keys para incluir `server_id` (evitar colisão de IDs entre servidores diferentes).

### 2.3. Motor de Ingestão (The Daemon)
O `SentinelDaemonV2` atual é um loop infinito único. Isso não escala para 100 ou 1000 servidores.
*   **Proposta:** Criar um **Manager de Ingestão**.
    *   O Manager consulta a tabela `servers` a cada X segundos.
    *   Para cada servidor ativo, ele despacha uma **Task Async** (ou utiliza um sistema de filas como Redis/Celery/Arq) para processar aquele servidor.
    *   Isso permite escalar horizontalmente: adicionar mais containers "Worker" conforme o número de clientes cresce.

---

## 3. Estrutura de Banco de Dados (Novas Tabelas)

Precisamos de um novo schema `core` ou `management` para gerenciar o SaaS:

### `saas_users`
Representa o cliente (Dono do Servidor).
- `id` (UUID)
- `email` (Unique)
- `hashed_password`
- `plan_tier` (Free, Pro, Enterprise)
- `stripe_customer_id`

### `saas_servers`
Representa uma conexão SFTP configurada.
- `id` (UUID)
- `owner_id` (FK saas_users)
- `name` (Ex: "Scum Server #1")
- `sftp_host`
- `sftp_port`
- `sftp_user`
- `sftp_password` (Encrypted)
- `sftp_path`
- `is_active` (Bool)
- `last_ingested_at` (Timestamp)
- `ingestion_status` (Healthy, Error, AuthFail)

### `saas_subscriptions`
Controle de pagamentos.
- `id`
- `user_id`
- `status` (active, canceled, past_due)
- `current_period_end`

---

## 4. O Desafio da Ingestão via SFTP

Como o SCUM geralmente é hospedado em provedores fechados (G-Portal, PingPerfect), não podemos instalar um "Agente" lá. Dependemos 100% de SFTP.
**Problema:** Manter 1000 conexões SFTP abertas simultaneamente é custoso e instável.

**Estratégia Híbrida (Polling Inteligente):**
1.  **Fase 1 (MVP):** Loop Async. Um único container roda loops para até ~50 servidores. Se crescer, subimos mais containers.
2.  **Otimização:** Em vez de `tail -f` (conexão persistente), fazemos **Polling Frequent**. Conecta -> Baixa diferença (bytes) -> Processa -> Desconecta.
    *   *Prós:* Menor uso de RAM/Socket. Recupera melhor de falhas de rede.
    *   *Contras:* Pequeno delay (ex: updates a cada 30s em vez de realtime). Para um Dashboard "Live", 30s é aceitável.

---

## 5. Roadmap de Implementação

### Fase 1: Preparação do Core (Refatoração)
1.  [Backend] Criar tabelas `saas_users` e `saas_servers`.
2.  [Backend] Adicionar `server_id` em todas as models do Sentinel.
3.  [Backend] Migrar o `SentinelDaemonV2` para aceitar um objeto `ServerConfig` como argumento, em vez de ler settings globais.

### Fase 2: O Manager
1.  [Backend] Criar o `IngestionManager`:
    ```python
    while True:
        servers = db.get_active_servers()
        for server in servers:
            if not server.is_being_processed():
                asyncio.create_task(process_server(server))
        await sleep(10)
    ```
2.  [API] Atualizar endpoints para exigir contexto. Ex: `GET /api/v2/{server_id}/kills`.

### Fase 3: Camada de Produto (Frontend)
1.  [Frontend] Criar Tela de Login / Registro.
2.  [Frontend] Dashboard "Meus Servidores" (CRUD de credenciais SFTP).
3.  [Frontend] Seletor de Servidor no Header (Context Switcher).

### Fase 4: Monetização
1.  Integração com Stripe (Checkout & Webhooks).
2.  Limites via código (Ex: Plano Free = Apenas 1 Servidor, Retenção 7 dias).

---

## 6. Estimativa de Esforço

*   **Backend Refactor:** 2-3 Semanas (Devido à complexidade de migrar 24 tabelas e garantir que o parser não quebre).
*   **Ingestion Engine:** 1-2 Semanas.
*   **Frontend SaaS Features:** 2 Semanas.
*   **Infra & Deploy:** 1 Semana.

**Total:** ~1.5 a 2 Meses para um MVP sólido.
