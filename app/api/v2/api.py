from fastapi import APIRouter
from app.api.v2.endpoints import (
    login, kills, admin, violations, chat, 
    economy, economy_extended, economy_analytics, economy_new_tables, economy_public,
    kills_analytics, system, monitoring, gameplay, registry, notifications, subscriptions
)

api_router = APIRouter()

# Logs V2
api_router.include_router(login.router, prefix="/logs/login", tags=["Logs V2 (Login)"])
api_router.include_router(kills.router, prefix="/logs/kills", tags=["Logs V2 (Kills)"])
api_router.include_router(admin.router, prefix="/logs/admin", tags=["Logs V2 (Admin)"])
api_router.include_router(violations.router, prefix="/logs/violations", tags=["Logs V2 (Violations)"])
api_router.include_router(chat.router, prefix="/logs/chat", tags=["Logs V2 (Chat)"])
api_router.include_router(economy.router, prefix="/logs/economy", tags=["Logs V2 (Economy)"])
api_router.include_router(economy_extended.router, prefix="/logs/economy-extended", tags=["Logs V2 (Economy Extended)"])

# Gameplay
api_router.include_router(gameplay.router, prefix="/logs/gameplay", tags=["Logs V2 (Gameplay)"])

# Analytics
api_router.include_router(economy_analytics.router, prefix="/analytics/economy", tags=["Analytics (Economy)"])
api_router.include_router(economy_new_tables.router, prefix="/analytics/economy-new", tags=["Analytics (Economy - New Tables)"])
api_router.include_router(economy_public.router, prefix="/public/economy", tags=["Analytics (Public Economy)"])
api_router.include_router(kills_analytics.router, tags=["Analytics (Kills)"])

# System
api_router.include_router(system.router, prefix="/system", tags=["System Monitoring"])

# Monitoring
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["System Monitoring"])

# Registry (Admin Dashboard)
api_router.include_router(registry.router, prefix="/admin/registry", tags=["Admin (Registry)"])

api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

# Subscriptions
api_router.include_router(subscriptions.router, prefix="/admin/subscriptions", tags=["Admin (Subscriptions)"])

# Access Requests (Public & Admin)
from app.api.v2.endpoints import access_requests, verification
api_router.include_router(access_requests.router, prefix="/access", tags=["Access Requests"])
api_router.include_router(verification.router, prefix="/verification", tags=["Verification"])


