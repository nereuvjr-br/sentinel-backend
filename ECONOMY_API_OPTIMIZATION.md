# ⚡ Otimização da API de Economia v2.2 (Public Safe & High Performance)

## 🔒 Princípio de Design: "Public Safe"
Como o dashboard `/logs/economy` é acessível a todos os jogadores, a API deve ser blindada para **não vazar informações sensíveis**.
*   ❌ **SEM Alertas:** Jogadores não podem ver exploits ou suspeitas de duping.
*   ❌ **SEM Detalhes de Transação:** Apenas agregados.
*   ❌ **SEM Dados em Tempo Real:** Cache mínimo de 5~10 minutos para evitar manipulação de mercado.

---

## 🏗️ Nova Arquitetura de Endpoints (Pública)

### 1. Endpoint Unificado: `GET /api/v2/public/economy/dashboard`

Este endpoint entrega **apenas** o necessário para renderizar a página pública, já calculado e seguro.

**Response Payload:**
```json
{
  "server_summary": {
    "total_cash": { "value": 1500000, "formatted": "$ 1.5M" },
    "total_bank": { "value": 5000000, "formatted": "$ 5.0M" },
    "total_gold": { "value": 2500, "formatted": "2.5K g" },
    "active_market_participants": 142
  },
  "market_trends": {
    "most_traded_item": { "name": "M82A1", "volume": 15 },
    "most_valuable_item": { "name": "C4", "avg_price": "$ 2.500" }
  },
  "top_items_sold": [
    // Apenas Top 10 fixo. Sem paginação infinita.
    { "rank": 1, "name": "9mm Ammo", "qty": 5000, "total_value": "$ 10.000" },
    // ...
  ],
  "top_items_bought": [
    // Apenas Top 10 fixo.
    { "rank": 1, "name": "Lockpick", "qty": 200, "total_value": "$ 50.000" },
    // ...
  ],
  "meta": {
    "updated_at": "19:30",
    "next_update": "19:35" // Cache de 5 min explícito
  }
}
```

---

## 🛡️ Camada de Segurança (Backend Service)

Criar `app/services/public_economy_service.py` que atua como **Firewall de Dados**:

1.  **Filtragem de Campos:**
    *   Nunca repassar `steam_id` de compradores/vendedores em listas públicas de itens.
    *   Nunca expor `wallet_id` ou saldos individuais de jogadores que não estejam num Leaderboard explícito.

2.  **Rate Limiting Oculto (Caching):**
    *   O service verifica se o cache do Redis (ou memória) tem menos de 5 minutos. Se tiver, retorna o cache.
    *   Isso impede que um player fique dando F5 para tentar descobrir quando um item raro foi vendido.

---

## 📅 Roteiro de Implementação (Focado em Público)

1.  **Backend:**
    *   Implementar `PublicEconomyService.get_dashboard_data()`.
    *   Configurar queries com `LIMIT 10` forçado.

2.  **Frontend (`/logs/economy`):**
    *   Substituir chamadas individuais (`useServerStats`, `useTopItems`) por `usePublicEconomyDashboard()`.
    *   Remover cards sensíveis ou lógicas de cálculo cliente-side.

Essa abordagem garante que a página seja leve, rápida e, acima de tudo, **segura para o público geral**.
