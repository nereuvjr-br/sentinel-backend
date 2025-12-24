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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
