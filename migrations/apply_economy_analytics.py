"""
Script para aplicar migração das tabelas de análise econômica
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession

async def apply_migration():
    # Ler o arquivo SQL
    with open('migrations/add_economy_analytics_tables.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Remover comentários de linha
    lines = []
    for line in sql_content.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('--'):
            lines.append(line)
    
    clean_sql = '\n'.join(lines)
    
    # Dividir em comandos (por CREATE TABLE, CREATE INDEX, COMMENT)
    import re
    commands = re.split(r';\s*(?=CREATE|COMMENT)', clean_sql)
    commands = [cmd.strip() + ';' for cmd in commands if cmd.strip()]
    
    async with AsyncSession(engine) as session:
        try:
            print(f"🚀 Aplicando {len(commands)} comandos SQL...")
            
            success_count = 0
            for idx, cmd in enumerate(commands, 1):
                if not cmd or len(cmd) < 10:
                    continue
                    
                try:
                    await session.execute(text(cmd))
                    success_count += 1
                    # Mostrar apenas CREATE TABLE
                    if 'CREATE TABLE' in cmd:
                        table_name = re.search(r'CREATE TABLE.*?(sentinel_\w+)', cmd)
                        if table_name:
                            print(f"  ✅ Tabela criada: {table_name.group(1)}")
                except Exception as e:
                    error_msg = str(e)
                    if 'already exists' in error_msg:
                        print(f"  ℹ️  Tabela/índice já existe (pulando)")
                    else:
                        print(f"  ⚠️  Erro: {error_msg[:80]}")
            
            await session.commit()
            print(f"\n✅ Migração concluída! {success_count} comandos executados com sucesso.")
            
        except Exception as e:
            print(f"\n❌ Erro ao aplicar migração: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(apply_migration())
