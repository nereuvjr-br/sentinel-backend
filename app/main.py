from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.endpoints import (
    logs, stats, login, violations, admin, economy, 
    vehicles, chests, gameplay, fame
)

app = FastAPI(
    title="SCUM Sentinel API",
    version="9.2.0",
    description="API de Inteligência de Dados para Servidores SCUM",
    docs_url=None,
    redoc_url=None,
)

# --- CORS ---
# Permite acesso do Frontend (Next.js) em desenvolvimento
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "https://scumoblivion.com.br",
    "https://www.scumoblivion.com.br",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTES ---
# Prefixamos todas as rotas da V1
app.include_router(logs.router, prefix="/v1/logs", tags=["Logs (General)"])
app.include_router(login.router, prefix="/v1/logs/login", tags=["Logs (Login)"])
app.include_router(violations.router, prefix="/v1/logs/violations", tags=["Logs (Violations)"])
app.include_router(admin.router, prefix="/v1/logs/admin", tags=["Logs (Admin)"])
app.include_router(economy.router, prefix="/v1/logs/economy", tags=["Logs (Economy)"])
app.include_router(vehicles.router, prefix="/v1/logs/vehicles", tags=["Logs (Vehicles)"])
app.include_router(chests.router, prefix="/v1/logs/chests", tags=["Logs (Chests)"])
app.include_router(gameplay.router, prefix="/v1/logs/gameplay", tags=["Logs (Gameplay)"])
app.include_router(fame.router, prefix="/v1/logs/fame", tags=["Logs (Fame)"])

app.include_router(stats.router, prefix="/v1/stats", tags=["Statistics & Intelligence"])

# --- V2 API (New Sentinel Daemon) ---
from app.api.v2.api import api_router as api_router_v2
app.include_router(api_router_v2, prefix="/v2")

# --- STATIC FILES (Dashboard) ---
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/admin", StaticFiles(directory=static_dir, html=True), name="static")

@app.on_event("startup")
async def startup_event():
    from app.services.queue_service import notification_queue
    await notification_queue.start_worker()

@app.get("/health")
def health_check():
    """Rota de verificação de status para Docker/K8s."""
    return {"status": "ok", "env": settings.ENV}

if __name__ == "__main__":
    import uvicorn
    # Entrypoint para debug direto via python app/main.py
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
