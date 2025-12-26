import os
import paramiko
import logging
from app.core.config import settings

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogDownloaderService:
    def __init__(self, local_dir: str = "logs"):
        """
        Inicializa o serviço de download de logs.
        Define os diretórios e credenciais SFTP.
        """
        self.local_dir = os.path.join(os.getcwd(), local_dir)
        self.host = settings.SFTP_HOST
        self.port = int(settings.SFTP_PORT)
        self.username = settings.SFTP_USER
        self.password = settings.SFTP_PASS
        self.remote_dir = settings.SFTP_PATH
        
        # Garante que o diretório local exista
        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir)
            logger.info(f"Diretório local criado: {self.local_dir}")

    def sync_logs(self):
        """
        Conecta ao SFTP e baixa arquivos de log novos ou atualizados.
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            logger.info(f"Conectando ao SFTP {self.host}...")
            ssh.connect(self.host, self.port, self.username, self.password)
            sftp = ssh.open_sftp()
            
            logger.info(f"Listando arquivos em {self.remote_dir}...")
            try:
                files = sftp.listdir_attr(self.remote_dir)
            except FileNotFoundError:
                logger.error(f"Diretório remoto não encontrado: {self.remote_dir}")
                return

            for file_attr in files:
                filename = file_attr.filename
                
                # Filtra apenas arquivos .log
                if not filename.endswith('.log'):
                    continue
                    
                remote_path = f"{self.remote_dir}/{filename}"
                local_path = os.path.join(self.local_dir, filename)
                
                remote_size = file_attr.st_size
                
                should_download = False
                
                if not os.path.exists(local_path):
                    logger.info(f"Novo arquivo encontrado: {filename}")
                    try:
                        sftp.get(remote_path, local_path)
                        logger.info(f"Download completo: {filename}")
                    except Exception as e:
                        logger.error(f"Erro ao baixar novo arquivo {filename}: {e}")
                else:
                    local_size = os.path.getsize(local_path)
                    if remote_size > local_size:
                        logger.info(f"Atualizando arquivo: {filename} (Local: {local_size} -> Remoto: {remote_size})")
                        try:
                            with sftp.open(remote_path, 'rb') as remote_file:
                                remote_file.seek(local_size)
                                new_data = remote_file.read()
                                with open(local_path, 'ab') as local_file:
                                    local_file.write(new_data)
                            logger.info(f"Arquivo atualizado com sucesso: {filename}")
                        except Exception as e:
                            logger.error(f"Erro ao atualizar arquivo {filename}: {e}")
                    elif remote_size < local_size:
                         logger.warning(f"Arquivo remoto menor que local (Rotação?): {filename}. Baixando novamente.")
                         try:
                             sftp.get(remote_path, local_path)
                         except Exception as e:
                             logger.error(f"Erro ao re-baixar {filename}: {e}")

        except Exception as e:
            logger.error(f"Erro na conexão SFTP: {e}")
        finally:
            ssh.close()

if __name__ == "__main__":
    downloader = LogDownloaderService()
    downloader.sync_logs()
