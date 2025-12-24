# SCUM Sentinel Backend (V9.3)

Este diretório contém a versão isolada e refatorada do Backend do SCUM Sentinel.

## Estrutura
- **app/**: Código fonte da aplicação.
    - **api/**: Endpoints FastAPI (V1/Logs).
    - **core/**: Configurações e Database Connection.
    - **models/**: Definições SQLModel (incluindo novos campos Anti-Cheat).
    - **services/**: Lógica de negócio (Sentinel Daemon e Parsers).
- **start.sh**: Script para iniciar API + Sentinel.
- **requirements.txt**: Dependências Python.

## Como Rodar
```bash
./start.sh
```

## Features Ativas
1.  **Anti-Cheat Parsing**: Detecção de Silent Aim, God Mode e Infrações com contagem.
2.  **Raid Radar**: Monitoramento de Lockpicking e C4 (Defusing).
3.  **Economy Intelligence**: Rastreamento detalhado de items e saldo bancário.
