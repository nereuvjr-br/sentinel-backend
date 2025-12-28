
import shutil
import os
import glob
import logging
from ingest_local_backups import ingest_backups
import asyncio

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("emergency_restore")

TARGET_DIR = r"C:\Servers\logs\logs\novos"
SOURCE_1 = r"C:\Users\nnvlj\scm-sentinel\sentinel-backend\logs"
SOURCE_2 = r"C:\Servers\logs\logs"
SOURCE_3 = r"C:\Servers\scum\SCUM\Saved\SaveFiles\Logs"

def emergency_restore():
    logger.warning("🚨 INICIANDO RESTAURAÇÃO DE EMERGÊNCIA 🚨")
    
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        logger.info(f"📁 Diretório alvo recriado: {TARGET_DIR}")

    count = 0
    
    # Fonte 1: Backup no Workspace (Mais recente)
    files_s1 = glob.glob(os.path.join(SOURCE_1, "*.log"))
    logger.info(f"🔎 Fonte 1 (Workspace): Encontrados {len(files_s1)} arquivos.")
    for f in files_s1:
        try:
            shutil.copy2(f, TARGET_DIR)
            count += 1
        except Exception as e:
            logger.error(f"Erro ao copiar {f}: {e}")

    # Fonte 2: Logs antigos na raiz (Dec 21)
    files_s2 = glob.glob(os.path.join(SOURCE_2, "*.log"))
    logger.info(f"🔎 Fonte 2 (Raiz Logs): Encontrados {len(files_s2)} arquivos.")
    for f in files_s2:
        try:
            # Evitar sobrescrever se já existir versão mais nova (pouco provável dado o wipe, mas seguro)
            dest_file = os.path.join(TARGET_DIR, os.path.basename(f))
            if not os.path.exists(dest_file):
                shutil.copy2(f, TARGET_DIR)
                count += 1
        except Exception as e:
            logger.error(f"Erro ao copiar {f}: {e}")

    # Fonte 3: Logs recuperados na pasta do servidor (Dec 22)
    files_s3 = glob.glob(os.path.join(SOURCE_3, "*.log"))
    logger.info(f"🔎 Fonte 3 (Server Saving): Encontrados {len(files_s3)} arquivos.")
    for f in files_s3:
        try:
            dest_file = os.path.join(TARGET_DIR, os.path.basename(f))
            if not os.path.exists(dest_file):
                shutil.copy2(f, TARGET_DIR)
                count += 1
        except Exception as e:
            logger.error(f"Erro ao copiar {f}: {e}")
            
    logger.info(f"✅ Arquivos restaurados para 'novos': {count}")
    
    # Criar relatório de datas
    from datetime import datetime
    import re
    
    found_dates = set()
    all_restored = glob.glob(os.path.join(TARGET_DIR, "*.log"))
    date_pattern = re.compile(r"(\d{8})")
    
    for f in all_restored:
        match = date_pattern.search(f)
        if match:
            found_dates.add(match.group(1))
            
    found_dates_sorted = sorted(list(found_dates))
    logger.info(f"📅 Datas recuperadas: {found_dates_sorted}")
    
    with open("MISSING_DATA_REPORT.md", "w") as report:
        report.write("# Relatório de Dados Recuperados\n\n")
        report.write("## Datas Encontradas e Processadas:\n")
        for d in found_dates_sorted:
            report.write(f"- {d}\n")
            
        report.write("\n## Datas Potencialmente Faltantes (Baseado em Gap):\n")
        # Simple gap check logic could go here, but for now just listing what we have is safer
        if '20251223' not in found_dates:
             report.write("- 20251223 (Nenhum log encontrado)\n")
        if '20251222' not in found_dates and len(files_s3) == 0:
             report.write("- 20251222 (Apenas parcial ou ausente se files_s3 falhou)\n")

    
    if count > 0:
        logger.info("🚀 Iniciando ingestão dos logs restaurados...")
        asyncio.run(ingest_backups())
    else:
        logger.warning("⚠️ Nenhum arquivo encontrado para restaurar.")

if __name__ == "__main__":
    emergency_restore()
