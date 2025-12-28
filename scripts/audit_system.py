
import asyncio
from sqlalchemy import text, select
from app.core.database import engine
from app.models.system_v2 import SentinelProcessedFile
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Silenciar logs
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)

async def audit_system():
    async with AsyncSession(engine) as session:
        print("\n=== AUDITORIA DO SISTEMA ===\n")
        
        # 1. TABELAS
        tables = [
            'sentinel_kills', 'sentinel_logins', 'sentinel_chat_messages',
            'sentinel_economy_trades', 'sentinel_violations', 'sentinel_processed_files',
            'sentinel_unparsed_logs'
        ]
        
        print(f"{'TABELA':<30} | COUNT")
        print("-" * 40)
        for t in tables:
            try:
                res = await session.execute(text(f"SELECT COUNT(*) FROM {t}"))
                print(f"{t:<30} | {res.scalar()}")
            except Exception as e:
                print(f"{t:<30} | ERRO: {e}")

        # 2. ARQUIVOS PROCESSADOS
        print("\n=== ARQUIVOS PROCESSADOS (Últimos 20) ===")
        stmt = select(SentinelProcessedFile).order_by(SentinelProcessedFile.last_modified.desc()).limit(20)
        res = await session.execute(stmt)
        files = res.scalars().all()
        
        for f in files:
            print(f"[{f.log_type}] {f.filename} -> Lines: {f.lines_processed}, Bytes: {f.processed_bytes}")

        # 3. VERIFICAR SE EXISTE ARQUIVO DE VIOLATION
        print("\n=== BUSCA POR ARQUIVOS DE VIOLATION ===")
        all_files_res = await session.execute(select(SentinelProcessedFile))
        all_files = all_files_res.scalars().all()
        
        found_violation_file = False
        for f in all_files:
            if "violation" in f.filename.lower():
                print(f"ACHOU: {f.filename} (Type: {f.log_type}) - Lines: {f.lines_processed}")
                found_violation_file = True
        
        if not found_violation_file:
            print("NENHUM ARQUIVO COM 'violation' NO NOME ENCONTRADO NA TABELA sentinel_processed_files!")

        # 4. CHECAR SE EXISTEM UNPARSED LOGS DE VIOLATION
        print("\n=== UNPARSED LOGS (Amostra) ===")
        res = await session.execute(text("SELECT filename, raw_line FROM sentinel_unparsed_logs LIMIT 5"))
        rows = res.fetchall()
        for r in rows:
            print(f"File: {r.filename} | Line: {r.raw_line[:50]}...")

if __name__ == "__main__":
    try:
        asyncio.run(audit_system())
    except Exception as e:
        print(f"CRASH NO SCRIPT: {e}")
