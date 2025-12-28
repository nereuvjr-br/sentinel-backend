"""
Script para verificar quais tabelas estão vazias no banco de dados
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

async def check_empty_tables():
    # Pegar DATABASE_URL do .env
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL não encontrada no .env")
        return
    
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        # Buscar todas as tabelas que começam com 'sentinel_'
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'sentinel_%'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result.fetchall()]
        
        print(f"\n📊 VERIFICANDO {len(tables)} TABELAS SENTINEL:\n")
        print("=" * 80)
        
        empty_tables = []
        populated_tables = []
        
        for table in tables:
            try:
                count_result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                
                status = "✅" if count > 0 else "❌"
                count_str = f"{count:,}" if count > 0 else "VAZIA"
                
                print(f"{status} {table:45} {count_str:>15} registros")
                
                if count == 0:
                    empty_tables.append(table)
                else:
                    populated_tables.append((table, count))
            except Exception as e:
                print(f"⚠️  {table:45} ERRO: {str(e)[:30]}")
        
        print("\n" + "=" * 80)
        print(f"\n📈 RESUMO:")
        print(f"   ✅ Tabelas populadas: {len(populated_tables)}")
        print(f"   ❌ Tabelas vazias: {len(empty_tables)}")
        
        if empty_tables:
            print(f"\n❌ TABELAS VAZIAS ({len(empty_tables)}):")
            for table in empty_tables:
                print(f"   - {table}")
        
        if populated_tables:
            print(f"\n✅ TOP 5 TABELAS MAIS POPULADAS:")
            sorted_tables = sorted(populated_tables, key=lambda x: x[1], reverse=True)[:5]
            for table, count in sorted_tables:
                print(f"   {count:>10,} - {table}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_empty_tables())
