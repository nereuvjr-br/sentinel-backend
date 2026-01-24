import asyncio
import sys
import os

# Adiciona o diretório atual ao path para resolver imports
sys.path.append(os.getcwd())

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.core.config import settings
from app.models.players_registry_v2 import SentinelPlayerRegistry
from app.models.gameplay_v2 import SentinelRaidMinigame
from app.services.notification_service import notification_service

# Forçar configurações para o teste
settings.EVOLUTION_API_URL = "http://localhost:8080"
settings.EVOLUTION_API_TOKEN = "Evo_2025_nRjr_9K4mL7xP2wQ5vF8hN3bT6cZ1yG0sA"
settings.EVOLUTION_INSTANCE_NAME = "novo-teste-1812"

async def run_simulation():
    print("Iniciando simulação de Raid...")
    
    # Dados de Teste
    target_steam_id = "76561198254469454"
    target_phone = "5577998094395" # Número mantido para recebimento do teste
    
    # O usuário informou que o Steam ID já está cadastrado com telefone no banco.
    # Pulando etapa de criação/atualização de usuário.
    print(f"ℹ️ Usando dados existentes no banco para SteamID: {target_steam_id}")

    # 2. Criar objeto de evento Raid
    raid_event = SentinelRaidMinigame(
        timestamp=datetime.utcnow(),
        attacker_steam_id="76561198012345678",
        attacker_name="Invasor Simulado",
        target_owner_steam_id=target_steam_id,
        target_owner_name="Vitima Teste (Sentinel AI)",
        minigame_class="LockpickingMinigame_C",
        target_object="BasicDoor",
        lock_type="Gold Lock",
        is_success=False, # False gera alerta de tentativa, True gera de violação
        failed_attempts=3,
        elapsed_time=12.5,
        location={"x": 100.0, "y": 200.0, "z": 300.0}
    )

    # 3. Chamar o serviço de notificação
    print("🚀 Enviando evento para NotificationService...")
    try:
        await notification_service.process_raid_event(raid_event)
        print("✅ Evento processado! Verifique seu WhatsApp.")
    except Exception as e:
        print(f"❌ Erro ao processar evento: {e}")

if __name__ == "__main__":
    asyncio.run(run_simulation())
