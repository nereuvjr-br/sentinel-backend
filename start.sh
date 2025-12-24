#!/bin/bash

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}>>> Iniciando SCUM Sentinel (Backend V2)...${NC}"

# Cleanup
cleanup() {
    echo -e "${BLUE}>>> Encerrando serviços...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}
trap cleanup SIGINT SIGTERM

# Activate Venv (assumes one level up or created inside backend)
# Tries local venv first, then parent
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
else
    echo "⚠️ VENV não encontrado. Tentando rodar com python do sistema..."
fi

# 1. API
echo -e "${GREEN}[1/2] Iniciando API Server...${NC}"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
PID_API=$!

# 2. Sentinel Daemon
echo -e "${GREEN}[2/2] Iniciando Log Sentinel...${NC}"
python sentinel_v2.py &
PID_SENTINEL=$!

# Wait
wait $PID_API $PID_SENTINEL
