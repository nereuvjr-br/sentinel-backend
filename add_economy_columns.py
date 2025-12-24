#!/usr/bin/env python3
"""
Script para adicionar as novas colunas nas tabelas existentes de economia.
"""

import sys
import asyncio
sys.path.insert(0, '/home/nereu-jr/Área de trabalho/scum/SCUMSentinel/backend')

from sqlalchemy import text
from app.core.database import engine

async def add_columns():
    """Adiciona novas colunas nas tabelas existentes"""
    print("🔧 Adicionando novas colunas nas tabelas de economia...")
    print()
    
    queries = [
        # sentinel_economy_trades
        "ALTER TABLE sentinel_economy_trades ADD COLUMN IF NOT EXISTS account_number VARCHAR",
        "ALTER TABLE sentinel_economy_trades ADD COLUMN IF NOT EXISTS item_health FLOAT",
        "ALTER TABLE sentinel_economy_trades ADD COLUMN IF NOT EXISTS item_uses INTEGER",
        "ALTER TABLE sentinel_economy_trades ADD COLUMN IF NOT EXISTS is_mechanic_service BOOLEAN DEFAULT FALSE",
        "ALTER TABLE sentinel_economy_trades ADD COLUMN IF NOT EXISTS pos_x FLOAT",
        "ALTER TABLE sentinel_economy_trades ADD COLUMN IF NOT EXISTS pos_y FLOAT",
        "ALTER TABLE sentinel_economy_trades ADD COLUMN IF NOT EXISTS pos_z FLOAT",
        
        # sentinel_economy_balances
        "ALTER TABLE sentinel_economy_balances ADD COLUMN IF NOT EXISTS account_number VARCHAR",
        "ALTER TABLE sentinel_economy_balances ADD COLUMN IF NOT EXISTS pos_x FLOAT",
        "ALTER TABLE sentinel_economy_balances ADD COLUMN IF NOT EXISTS pos_y FLOAT",
        "ALTER TABLE sentinel_economy_balances ADD COLUMN IF NOT EXISTS pos_z FLOAT",
    ]
    
    try:
        async with engine.begin() as conn:
            for query in queries:
                print(f"  Executando: {query[:60]}...")
                await conn.execute(text(query))
        
        print()
        print("✅ Colunas adicionadas com sucesso!")
        print()
        print("📊 Colunas adicionadas:")
        print("  sentinel_economy_trades:")
        print("    - account_number")
        print("    - item_health")
        print("    - item_uses")
        print("    - is_mechanic_service")
        print("    - pos_x, pos_y, pos_z")
        print()
        print("  sentinel_economy_balances:")
        print("    - account_number")
        print("    - pos_x, pos_y, pos_z")
        
    except Exception as e:
        print(f"❌ Erro ao adicionar colunas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(add_columns())
    sys.exit(0 if success else 1)
