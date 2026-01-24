import asyncio
from app.core.logger import logger
from app.services.scum_db_service import scum_db_service

async def main():
    logger.info("🔄 Iniciando Sentinel DB Sync Service (Processo Isolado)...")
    try:
        await scum_db_service.run_sync_loop()
    except KeyboardInterrupt:
        logger.info("🛑 DB Sync Service interrompido pelo usuário.")
    except Exception as e:
        logger.critical(f"❌ Erro crítico no DB Sync Service: {e}")

if __name__ == "__main__":
    asyncio.run(main())
