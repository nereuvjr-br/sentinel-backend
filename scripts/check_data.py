"""
Script para verificar se há dados nas tabelas
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def check_data():
    tables_with_timestamp = [
        ('sentinel_kills', 'timestamp'),
        ('sentinel_logins', 'timestamp'),
        ('sentinel_chat_messages', 'timestamp'),
        ('sentinel_economy_trades', 'timestamp'),
        ('sentinel_admin_commands', 'timestamp'),
    ]
    
    async with AsyncSession(engine) as session:
        print("📊 Verificando dados nas tabelas...\n")
        
        total_records = 0
        
        for table, ts_col in tables_with_timestamp:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            total_records += count
            
            if count > 0:
                print(f"✅ {table:35} : {count:6} registros")
                
                # Mostrar último registro
                try:
                    result = await session.execute(
                        text(f"SELECT * FROM {table} ORDER BY {ts_col} DESC LIMIT 1")
                    )
                    last = result.fetchone()
                    if last and len(last) > 0:
                        print(f"   Último timestamp: {last[0]}")
                except Exception as e:
                    print(f"   Erro ao buscar último: {e}")
            else:
                print(f"❌ {table:35} : {count:6} registros (VAZIO)")
        
        print(f"\n📊 TOTAL DE REGISTROS: {total_records}")
        
        # Verificar processed_files
        print("\n📁 Arquivos processados:")
        result = await session.execute(
            text("SELECT filename, last_offset, last_size FROM sentinel_processed_files ORDER BY last_processed DESC LIMIT 10")
        )
        files = result.fetchall()
        
        if files:
            for f in files:
                print(f"  - {f[0]:40} | Offset: {f[1]:8} | Size: {f[2]:8}")
        else:
            print("  ⚠️  Nenhum arquivo processado ainda")

if __name__ == "__main__":
    asyncio.run(check_data())
