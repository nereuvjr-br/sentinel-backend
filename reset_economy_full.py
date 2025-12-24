#!/usr/bin/env python3
"""
Script para resetar COMPLETAMENTE a economia e reprocessar LOGOS desde o início.
REALIZA TRUNCATE NAS TABELAS DE ECONOMIA e reseta o tracking dos arquivos.
"""

import sys
import asyncio
sys.path.insert(0, '/home/nereu-jr/Área de trabalho/scum/SCUMSentinel/backend')

from sqlalchemy import text
from app.core.database import engine

async def full_wipe_and_reset_economy():
    """
    1. Truncate nas tabelas de economia.
    2. Reset na tabela de arquivos processados (apenas logs de Economy).
    """
    print("🚨 INICIANDO WIPE COMPLETO DOS DADOS DE ECONOMIA 🚨")
    print("===================================================")
    
    tables_to_truncate = [
        "sentinel_economy_trades",
        "sentinel_economy_balances",
        "sentinel_bank_transactions",
        "sentinel_mechanic_services",
        "sentinel_bank_cards",
        "sentinel_unparsed_logs"  # Opcional, mas bom para limpar sujeira
    ]
    
    try:
        async with engine.begin() as conn:
            # 1. Truncate Tables
            print("🗑️  Limpando tabelas de dados...")
            for table in tables_to_truncate:
                print(f"   - Truncating {table}...")
                # CASCADE para garantir que chaves estrangeiras não bloqueiem (se houver)
                # RESTART IDENTITY para resetar os IDs auto-increment
                await conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
            
            print("✅ Tabelas limpas com sucesso!")
            
            # 2. Reset Processed Files
            print("\n🔄 Resetando tracking dos arquivos de log...")
            result = await conn.execute(
                text("""
                    UPDATE sentinel_processed_files 
                    SET processed_bytes = 0, 
                        lines_processed = 0
                    WHERE log_type = 'Economy'
                    RETURNING filename
                """)
            )
            
            files = result.fetchall()
            
            if files:
                print(f"✅ {len(files)} arquivos marcados para reprocessamento:")
                for file in files:
                    print(f"   - {file[0]}")
            else:
                print("⚠️  Nenhum arquivo de log 'Economy' encontrado no tracking.")
            
            print("\n🚀 CONCLUÍDO! O sistema irá reprocessar os dados agora.")
            print("   Certifique-se que o backend está rodando.")
            
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(full_wipe_and_reset_economy())
    sys.exit(0 if success else 1)
