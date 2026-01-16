
import paramiko
import os
from app.core.config import settings
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sftp_restore")

LOCAL_DIR = "/root/sentinel-backend/logs/downloaded"

def restore_logs():
    logger.info("🔄 Iniciando restauração de logs do SFTP...")
    
    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)
        logger.info(f"📁 Diretório local criado: {LOCAL_DIR}")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(settings.SFTP_HOST, int(settings.SFTP_PORT), settings.SFTP_USER, settings.SFTP_PASS)
        sftp = ssh.open_sftp()
        
        remote_path = settings.SFTP_PATH
        if not remote_path:
            logger.error("❌ settings.SFTP_PATH não está definido no .env")
            return
            
        logger.info(f"✅ Usando caminho SFTP configurado: {remote_path}")

        files = sftp.listdir(remote_path)
        count = 0
        
        for file_name in files:
            # Filtra apenas arquivos de log relevantes se necessário (.log)
            if file_name.endswith('.log') or 'login' in file_name.lower() or 'chat' in file_name.lower() or 'kill' in file_name.lower() or 'economy' in file_name.lower():
                remote_file = f"{remote_path}/{file_name}"
                local_file = os.path.join(LOCAL_DIR, file_name)
                
                # Verifica se já existe para não baixar duplicado, ou baixa sempre para garantir
                if not os.path.exists(local_file):
                    logger.info(f"⬇️ Baixando: {file_name}")
                    sftp.get(remote_file, local_file)
                    count += 1
                else:
                    logger.debug(f"⏭️ Arquivo já existe: {file_name}")
        
        logger.info(f"✅ Restauração concluída. {count} arquivos baixados.")

    except Exception as e:
        logger.error(f"❌ Erro durante a restauração: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    restore_logs()
