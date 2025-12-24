import asyncio
from sqlmodel import SQLModel, create_engine
from app.models.admin_v2 import SentinelAdminCommand
from app.models.chat_v2 import SentinelChatMessage
from app.models.login_v2 import SentinelLogin
from app.models.kill_v2 import SentinelKill
from app.models.economy_v2 import SentinelEconomyTrade, SentinelEconomyBalance
from app.models.gameplay_v2 import SentinelRaidMinigame, SentinelCrafting, SentinelExplosiveEvent, SentinelBunkerEvent
from app.models.violation_v2 import SentinelViolation
from app.models.chest_fame_v2 import SentinelChestEvent, SentinelFameEvent
from app.models.system_v2 import SentinelProcessedFile
from app.core.config import settings

# Usando Sync Engine para DDL simples
db_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
engine = create_engine(db_url)

def init_db():
    print("🔨 Criando tabelas do Sentinel V2...")
    SQLModel.metadata.create_all(engine)
    print("✅ Tabela 'sentinel_admin_commands' criada (se não existia).")
    print("✅ Tabela 'sentinel_chat_messages' criada (se não existia).")
    print("✅ Tabela 'sentinel_logins' criada (se não existia).")
    print("✅ Tabela 'sentinel_kills' criada (se não existia).")
    print("✅ Tabelas de Economia criadas (se não existiam).")
    print("✅ Tabelas de Gameplay (Raid/Craft) criadas (se não existiam).")
    print("✅ Tabela 'sentinel_violations' criada (se não existia).")
    print("✅ Tabelas de Chest/Fame criadas (se não existiam).")

if __name__ == "__main__":
    init_db()
