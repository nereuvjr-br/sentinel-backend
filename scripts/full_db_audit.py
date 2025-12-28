
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Configuração Limpa
logging.basicConfig(level=logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

async def full_audit():
    print(f"\n{'TABELA':<40} | {'REGISTROS':<10} | STATUS")
    print("="*70)
    
    total_tables = 0
    non_empty_tables = 0
    
    async with AsyncSession(engine) as session:
        # 1. Obter lista de todas as tabelas no schema public
        query_tables = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        result = await session.execute(query_tables)
        tables = result.scalars().all()
        
        # 2. Contar registros de cada uma
        for table in tables:
            if table == "alembic_version": continue # Ignorar tabela de migração interna
            
            try:
                count_res = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_res.scalar()
                
                status_icon = "✅ ZERADA" if count == 0 else "📦 DADOS"
                if count > 0:
                    non_empty_tables += 1
                    
                print(f"{table:<40} | {count:<10} | {status_icon}")
                total_tables += 1
            except Exception as e:
                print(f"{table:<40} | ERRO       | {e}")

    print("="*70)
    print(f"Total Auditado: {total_tables} tabelas.")
    print(f"Tabelas com Dados: {non_empty_tables}")
    print(f"Tabelas Vazias: {total_tables - non_empty_tables}")
    print("\n")

if __name__ == "__main__":
    asyncio.run(full_audit())
