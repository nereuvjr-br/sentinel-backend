"""
Script para processar logs locais de C:\\Servers\\logs\\logs\\novos
Execute este script manualmente para processar logs locais
"""
import asyncio
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.services.parsers_v2.kill import KillParserV2
from app.services.parsers_v2.login import LoginParserV2
from app.services.parsers_v2.chat import ChatParserV2
from app.services.parsers_v2.economy import EconomyParserV2
from app.services.parsers_v2.admin import AdminParserV2
from app.services.parsers_v2.gameplay import GameplayParserV2
from app.services.parsers_v2.chest_fame import ChestFameParserV2
from app.services.parsers_v2.violation import ViolationParserV2
from app.services.parsers_v2.vehicle import VehicleParserV2

# Diretório local de logs
LOCAL_LOGS_DIR = r"C:\Servers\logs\logs\novos"

# Mapeamento de tipos de arquivo para parsers
PARSERS = {
    'kill': KillParserV2.parse,
    'login': LoginParserV2.parse,
    'chat': ChatParserV2.parse,
    'economy': EconomyParserV2.parse,
    'admin': AdminParserV2.parse,
    'gameplay': GameplayParserV2.parse,
    'chest': ChestFameParserV2.parse_chest,
    'fame': ChestFameParserV2.parse_fame,
    'violation': ViolationParserV2.parse,
    'vehicle': VehicleParserV2.parse,
}

def detect_log_type(filename: str) -> str:
    """Detecta o tipo de log baseado no nome do arquivo"""
    filename_lower = filename.lower()
    
    if 'kill' in filename_lower:
        return 'kill'
    elif 'login' in filename_lower:
        return 'login'
    elif 'chat' in filename_lower:
        return 'chat'
    elif 'economy' in filename_lower or 'trade' in filename_lower:
        return 'economy'
    elif 'admin' in filename_lower:
        return 'admin'
    elif 'gameplay' in filename_lower or 'raid' in filename_lower:
        return 'gameplay'
    elif 'chest' in filename_lower:
        return 'chest'
    elif 'fame' in filename_lower:
        return 'fame'
    elif 'violation' in filename_lower or 'anticheat' in filename_lower:
        return 'violation'
    elif 'vehicle' in filename_lower:
        return 'vehicle'
    else:
        return 'unknown'

async def process_log_file(filepath: Path, log_type: str, session: AsyncSession):
    """Processa um arquivo de log"""
    parser = PARSERS.get(log_type)
    
    if not parser:
        print(f"  ⚠️  Tipo de log desconhecido: {log_type}")
        return 0, 0
    
    parsed_count = 0
    error_count = 0
    batch = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    result = parser(line)
                    if result:
                        batch.append(result)
                        parsed_count += 1
                        
                        # Commit em lotes de 100
                        if len(batch) >= 100:
                            session.add_all(batch)
                            await session.commit()
                            batch = []
                            
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # Mostra apenas os primeiros 5 erros
                        print(f"    ⚠️  Erro na linha {line_num}: {str(e)[:80]}")
        
        # Commit final
        if batch:
            session.add_all(batch)
            await session.commit()
            
    except Exception as e:
        print(f"  ❌ Erro ao processar arquivo: {str(e)}")
        await session.rollback()
        return 0, 0
    
    return parsed_count, error_count

async def process_local_logs():
    """Processa todos os logs do diretório local"""
    print("🚀 Iniciando processamento de logs locais...")
    print(f"📂 Diretório: {LOCAL_LOGS_DIR}\n")
    
    # Verificar se o diretório existe
    logs_dir = Path(LOCAL_LOGS_DIR)
    if not logs_dir.exists():
        print(f"❌ Diretório não encontrado: {LOCAL_LOGS_DIR}")
        return
    
    # Listar arquivos .log
    log_files = list(logs_dir.glob("*.log"))
    
    if not log_files:
        print("⚠️  Nenhum arquivo .log encontrado no diretório")
        return
    
    print(f"📊 Encontrados {len(log_files)} arquivo(s) .log\n")
    
    # Processar cada arquivo
    total_parsed = 0
    total_errors = 0
    
    async with AsyncSession(engine) as session:
        for idx, filepath in enumerate(log_files, 1):
            filename = filepath.name
            log_type = detect_log_type(filename)
            
            print(f"[{idx}/{len(log_files)}] Processando: {filename}")
            print(f"  📋 Tipo detectado: {log_type}")
            
            if log_type == 'unknown':
                print(f"  ⏭️  Pulando arquivo (tipo desconhecido)\n")
                continue
            
            start_time = datetime.now()
            parsed, errors = await process_log_file(filepath, log_type, session)
            duration = (datetime.now() - start_time).total_seconds()
            
            total_parsed += parsed
            total_errors += errors
            
            print(f"  ✅ Processado: {parsed} registros")
            if errors > 0:
                print(f"  ⚠️  Erros: {errors}")
            print(f"  ⏱️  Tempo: {duration:.2f}s\n")
    
    # Resumo final
    print("=" * 60)
    print("✅ PROCESSAMENTO CONCLUÍDO!")
    print("=" * 60)
    print(f"📊 Total de arquivos processados: {len(log_files)}")
    print(f"✅ Total de registros salvos: {total_parsed}")
    if total_errors > 0:
        print(f"⚠️  Total de erros: {total_errors}")
    print("=" * 60)

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║     SENTINEL - Processador de Logs Locais V2            ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(process_local_logs())
