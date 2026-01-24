# Plano de Implementação: Sistema de Assinaturas e Notificações Customizáveis

## 1. Visão Geral
Implementar um sistema de monetização e controle granular de notificações (SaaS), permitindo diferenciar usuários **Free** (com delay) de usuários **Premium** (tempo real e completo).

## 2. Mudanças no Banco de Dados (Backend)

### A. Tabela `sentinel_plans` (Nova ou Enum/Campos)
Adicionar campos de assinatura aos modelos existentes ou criar uma tabela dedicada. Para simplificar e manter performance, vamos adicionar colunas aos modelos principais.

#### Atualizar `SentinelPlayerRegistry` (Players) e `SentinelClan` (Clãs)
Novos campos:
- `plan_tier`: Enum (`free`, `premium`) - Default: `free`
- `plan_expires_at`: DateTime (Nullable) - Data de vencimento.
- `notification_settings`: JSON - Configurações individuais (ex: ativar Raid, desativar Killfeed).
    ```json
    {
      "raid_alert": true,
      "killfeed": false,
      "base_decay": true
    }
    ```

### B. Tabela `sentinel_notification_queue` (Nova)
Para suportar o **delay** da versão grátis de forma robusta (sobrevivendo a restarts), não podemos apenas usar `sleep()`. Precisamos de uma fila persistente.
- `id`: PK
- `recipient_phone`: String
- `message_content`: String
- `scheduled_for`: DateTime (Quando deve ser enviado)
- `status`: `pending`, `processed`, `failed`
- `metadata`: JSON (Raid ID, Contexto)

## 3. Lógica de Backend (Serviços)

### A. Atualização do `NotificationService`
Lógica de verificação antes de enviar:
1.  **Checar Assinatura**:
    - Se `premium` e não expirado: Enviar `IMMEDIATE`.
    - Se `free` ou expirado:
        - Calcular Delay (ex: 15 minutos).
        - Salvar na `sentinel_notification_queue` com `scheduled_for = now + 15min`.
        - *Nota*: Apenas notificações críticas (Raid) talvez sofram delay. Avisos de Admin podem ser imediatos.

### B. Novo Worker: `QueueProcessor`
Um loop em background (`asyncio.create_task` no startup) que roda a cada 30s:
- Busca itens na fila onde `scheduled_for <= now` e `status = 'pending'`.
- Envia via Evolution API.
- Atualiza status para `processed`.

### C. API Endpoints (`/v2/subscriptions`)
- `POST /plans/assign`: Atribuir plano a SteamID ou ClanID.
- `GET /plans/status/{id}`: Consultar status.
- `PATCH /settings`: Usuário/Admin atualizar configs (JSON).

## 4. Interface Frontend (Next.js)

### A. Painel Administrativo (`/admin/subscriptions`)
- Lista de Jogadores/Clãs com status da assinatura.
- **Ações**:
    - "Ativar Premium" (Modal com seletor de duração: 1 mês, 3 meses, Permanente).
    - "Revogar Acesso".
    - "Editar Configurações" (Toggle de tipos de notificação).

### B. Componentes UI
- **StatusBadge**: Componente visual (`Free` cinza, `Premium` dourado/brilhante).
- **SubscriptionCard**: Card para editar os detalhes da assinatura.

## 5. Fluxo de Trabalho
1.  **Backend**: Criar migrations e atualizar Models.
2.  **Backend**: Implementar fila e worker de processamento.
3.  **Backend**: Atualizar lógica de envio no `NotificationService`.
4.  **Frontend**: Criar páginas de gestão de assinaturas.
