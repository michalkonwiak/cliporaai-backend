from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    redis_host: str
    redis_port: int

    celery_broker_url: str
    celery_result_backend: str

    host: str = "127.0.0.1"
    port: int = 8000

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    log_level: str = "INFO"
    log_file_path: str = "logs/app.log"
    enable_file_logging: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()  # type: ignore
