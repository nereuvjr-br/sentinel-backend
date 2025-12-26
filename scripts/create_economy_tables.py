#!/usr/bin/env python3
"""
Script para criar as novas tabelas do Economy Parser V2 no banco de dados.
"""

import sys
import asyncio
sys.path.insert(0, '/home/nereu-jr/Área de trabalho/scum/SCUMSentinel/backend')

from sqlmodel import SQLModel
from app.core.database import engine
from app.models.economy_v2 import (
    SentinelEconomyTrade,
    SentinelEconomyBalance,
    SentinelBankTransaction,
    SentinelMechanicService,
    SentinelBankCard,
    SentinelUnparsedLog
)

async def create_tables():
    """Cria todas as tabelas do banco de dados"""
    print("🔧 Criando tabelas do Economy Parser V2...")
    print()
    
    try:
        # Criar todas as tabelas
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        
        print("✅ Tabelas criadas com sucesso!")
        print()
        print("📊 Tabelas criadas:")
        print("  - sentinel_economy_trades (atualizada com novos campos)")
        print("  - sentinel_economy_balances (atualizada com novos campos)")
        print("  - sentinel_bank_transactions (NOVA)")
        print("  - sentinel_mechanic_services (NOVA)")
        print("  - sentinel_bank_cards (NOVA)")
        print("  - sentinel_unparsed_logs (NOVA)")
        print()
        print("🎯 Próximos passos:")
        print("  1. Verificar endpoints: curl http://localhost:8000/api/v2/logs/economy-extended/stats/")
        print("  2. Monitorar logs: tail -f /caminho/para/logs/sentinel_v2.log")
        print("  3. Aguardar dados serem capturados")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)
