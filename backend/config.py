from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    database_url: str
    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    reset_token_expire_minutes: int = 60

    mail_server: str = "localhost"
    mail_port: int = 2525
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = "3LM@example.com"
    mail_use_tls: bool = True

    frontend_url: str = "http://localhost:8000"
    ai_service_url: str = "http://localhost:8080"

    scheduler_interval_hours: int = 24
    generation_lookahead_days: int = 7

settings = Settings() 