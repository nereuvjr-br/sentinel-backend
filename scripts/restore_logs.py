
import paramiko
import os
from app.core.config import settings
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sftp_restore")

LOCAL_DIR = r"C:\Servers\logs\logs\novos"

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
        
        # Tenta listar o diretório correto. Baseado na estrutura anterior, parece ser Logs direto ou dentro da pasta do servidor
        # O output anterior mostrou /138.199.5.114_7122/Logs como uma possibilidade
        possible_paths = [
            '/138.199.5.114_7122/Logs',
            '/138.199.5.114_7122/SCUM/Saved/SaveFiles/Logs' 
        ]
        
        remote_path = None
        for p in possible_paths:
            try:
                sftp.listdir(p)
                remote_path = p
                logger.info(f"✅ Caminho de logs encontrado: {remote_path}")
                break
            except FileNotFoundError:
                continue
        
        if not remote_path:
            logger.error("❌ Nenhum caminho de logs válido encontrado no SFTP.")
            return

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
