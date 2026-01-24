from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # System
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_HOURS: int = 24
    TIMEZONE: str = "UTC"
    WIPE_DATE: Optional[str] = None

    # Database
    DATABASE_URL: str

    # SFTP
    SFTP_HOST: str
    SFTP_PORT: int
    SFTP_USER: Optional[str] = None
    SFTP_PASS: Optional[str] = None
    SFTP_PATH: str = "/138.199.5.114_7122/SaveFiles/Logs"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Webhooks
    DISCORD_WEBHOOK_ALERTS: Optional[str] = None
    DISCORD_WEBHOOK_KILLFEED: Optional[str] = None
    
    # Business Logic
    EXCLUDED_ITEMS: str = ""
    RAID_LOG_DELAY_MINUTES: int = 0
    SCUM_DB_SYNC_MINUTES: int = 15  # Default 15 min
    SCUM_DB_REMOTE_PATH: str = "SCUM.db"  # Relative to SFTP_PATH if inside SaveFiles, or absolute

    # Evolution API (WhatsApp)
    EVOLUTION_API_URL: Optional[str] = "http://localhost:8080"
    EVOLUTION_API_TOKEN: Optional[str] = None
    EVOLUTION_INSTANCE_NAME: Optional[str] = "Sentinel"


    @property
    def excluded_items_list(self) -> list[str]:
        if not self.EXCLUDED_ITEMS:
            return []
        return [item.strip() for item in self.EXCLUDED_ITEMS.split(",") if item.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
