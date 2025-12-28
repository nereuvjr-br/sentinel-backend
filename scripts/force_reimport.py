
import argparse
import asyncio
from sqlmodel import select
from app.core.database import engine
from app.models.system_v2 import SentinelProcessedFile
from sqlalchemy.ext.asyncio import AsyncSession

async def force_reimport(log_type=None, filename=None, dry_run=True):
    async with AsyncSession(engine) as session:
        # Construir query
        stmt = select(SentinelProcessedFile)
        
        conditions = []
        if log_type:
            # Case insensitive search para facilitar
            conditions.append(SentinelProcessedFile.log_type == log_type)
        if filename:
            conditions.append(SentinelProcessedFile.filename.contains(filename))
        
        if log_type:
            stmt = stmt.where(SentinelProcessedFile.log_type == log_type)
        if filename:
            stmt = stmt.where(SentinelProcessedFile.filename.contains(filename))

        # Executar busca
        results = await session.execute(stmt)
        files = results.scalars().all()
        
        print(f"\n--- 📂 Arquivos Rheados ({len(files)}) ---")
        for f in files:
            print(f" • [{f.log_type}] {f.filename} (Lidos: {f.processed_bytes} bytes)")
            
        if not files:
            print("⚠️ Nenhum arquivo encontrado com os filtros especificados.")
            print("Dica: Verifique se o nome do tipo está correto (Ex: Violation, Kill, Economy)")
            return

        if dry_run:
            print("\n🟡 [MODO SIMULAÇÃO]")
            print("Nenhuma alteração foi feita. O sistema NÃO irá re-ler estes arquivos ainda.")
            print("Para executar de verdade, adicione a flag: --confirm")
        else:
            print("\n🔴 [EXECUTANDO RESET]")
            count = 0
            for f in files:
                await session.delete(f)
                count += 1
            
            await session.commit()
            print(f"✅ Sucesso! {count} arquivos foram removidos do cache.")
            print("🔄 O Sentinel Daemon irá re-processar estes arquivos do ZERO no próximo ciclo.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentinel V2 - Ferramenta de Re-importação Forçada")
    parser.add_argument("--type", help="Filtrar por tipo de log (Ex: Violation, Kill, Economy, Chat, Login)")
    parser.add_argument("--file", help="Filtrar por parte do nome do arquivo (Ex: 2025.12.26)")
    parser.add_argument("--confirm", action="store_true", help="Confirma a execução (Desativa modo simulação)")
    
    args = parser.parse_args()
    
    if not args.type and not args.file:
        print("❌ Erro: Você deve especificar pelo menos --type ou --file")
        print("Exemplo: python scripts/force_reimport.py --type Violation")
    else:
        asyncio.run(force_reimport(log_type=args.type, filename=args.file, dry_run=not args.confirm))
