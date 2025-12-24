#!/usr/bin/env python3
"""
Script para reprocessar logs de economia e popular o banco com dados completos.
Força o processamento de logs antigos para capturar health, uses, coordenadas, etc.
"""

import sys
import asyncio
sys.path.insert(0, '/home/nereu-jr/Área de trabalho/scum/SCUMSentinel/backend')

from sqlalchemy import text
from app.core.database import engine

async def reset_economy_processing():
    """
    Reseta o estado de processamento dos arquivos de economia
    para forçar o reprocessamento com os novos parsers.
    """
    print("🔄 Resetando estado de processamento dos logs de economia...")
    print()
    
    try:
        async with engine.begin() as conn:
            # Resetar apenas arquivos de economia
            result = await conn.execute(
                text("""
                    UPDATE sentinel_processed_files 
                    SET processed_bytes = 0, 
                        lines_processed = 0
                    WHERE log_type = 'Economy'
                    RETURNING filename, processed_bytes
                """)
            )
            
            files = result.fetchall()
            
            if files:
                print(f"✅ {len(files)} arquivo(s) de economia resetados:")
                for file in files:
                    print(f"   - {file[0]}")
            else:
                print("⚠️  Nenhum arquivo de economia encontrado para resetar")
            
            print()
            print("📊 Próximos passos:")
            print("   1. O daemon vai reprocessar os logs automaticamente")
            print("   2. Aguarde ~30 segundos")
            print("   3. Verifique: curl http://localhost:8000/v2/logs/economy-extended/stats/")
            print()
            print("💡 Dica: Monitore os logs do daemon para ver o progresso")
            
    except Exception as e:
        print(f"❌ Erro ao resetar: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(reset_economy_processing())
    sys.exit(0 if success else 1)
