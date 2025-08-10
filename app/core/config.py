import os
from pathlib import Path
from typing import Literal

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")
except Exception:
    pass

from pydantic import AnyUrl, Field, PositiveInt, PostgresDsn, RedisDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database settings
    database_url: str | None = Field(
        None,
        description="Override: full async SQLAlchemy URL (e.g., sqlite+aiosqlite:///./test.db)",
    )
    postgres_dsn: PostgresDsn = Field(
        PostgresDsn("postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"),
        description="PostgreSQL connection string",
    )
    
    # Redis settings
    redis_dsn: RedisDsn = Field(RedisDsn("redis://localhost:6379/0"), description="Redis connection string")
    redis_decode_responses: bool = Field(False, description="Decode Redis responses as UTF-8 strings")

    # Celery settings
    celery_broker_url: AnyUrl | None = Field(None, description="Celery broker URL")
    celery_result_backend: AnyUrl | None = Field(None, description="Celery result backend URL")

    # Server settings
    environment: Literal["development", "staging", "production"] = Field("development", description="Runtime environment")
    host: str = Field("127.0.0.1", description="Host to bind the server to")
    port: PositiveInt = Field(8000, description="Port to bind the server to")
    auto_migrate: bool = Field(False, description="Automatically run migrations on startup")
    
    # CORS settings
    cors_origins: list[str] = Field(
        ["http://localhost:3000"], 
        description="List of allowed origins for CORS"
    )
    cors_allow_credentials: bool = Field(True, description="Allow credentials for CORS")
    cors_allow_methods: list[str] = Field(
        ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"], 
        description="List of allowed methods for CORS"
    )
    cors_allow_headers: list[str] = Field(
        [
            "Authorization", 
            "Content-Type", 
            "X-Request-ID",
            "Accept",
            "Origin",
            "X-Requested-With",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
            "Range",
            "Content-Range",
            "Content-Disposition"
        ], 
        description="List of allowed headers for CORS"
    )
    
    # Proxy settings
    trusted_hosts: list[str] = Field(
        ["cliporaai.com", "localhost", "127.0.0.1"],
        description="List of trusted hosts for proxy headers"
    )

    # Security settings
    secret_key: SecretStr | None = Field(SecretStr("dev-secret-key"), description="Secret key for HS256")
    algorithm: Literal["HS256", "RS256", "ES256"] = Field("HS256", description="Algorithm for JWT encoding")
    access_token_expire_minutes: PositiveInt = Field(30, description="JWT token expiration time in minutes")
    jwt_leeway_seconds: PositiveInt = Field(30, description="Leeway in seconds for JWT token validation")
    jwt_issuer: str = Field("cliporaai", description="Issuer claim for JWT tokens")
    jwt_audience: str = Field("cliporaai-api", description="Audience claim for JWT tokens")
    
    # JWT key paths for asymmetric algos
    jwt_private_key_path: str | None = Field(None, description="PEM private key for RS/ES")
    jwt_public_key_path: str | None = Field(None, description="PEM public key for RS/ES")
    jwt_kid: str | None = Field(None, description="Optional key ID (kid) to include in JWT headers and to select keys")

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", description="Logging level"
    )
    log_file_path: str = Field("logs/app.log", description="Path to log file")
    enable_file_logging: bool = Field(True, description="Enable file logging")

    # File storage settings
    storage_type: Literal["local", "s3"] = Field(
        "local", description="Storage type (local or s3)"
    )
    upload_dir: str = Field("uploads", description="Directory for file uploads")
    temp_upload_dir: str = Field("uploads/temp", description="Directory for temporary file uploads")
    
    # S3 settings (used if storage_type is 's3')
    s3_bucket_name: str | None = None
    s3_region: str | None = None
    aws_access_key_id: SecretStr | None = None
    aws_secret_access_key: SecretStr | None = None
    s3_endpoint_url: AnyUrl | None = None
    
    # Connection settings
    connection_timeout: PositiveInt = Field(5, description="Connection timeout in seconds")
    max_retries: PositiveInt = Field(3, description="Maximum number of retries for connections")
    retry_backoff: float = Field(0.5, description="Backoff factor for retries")
    
    # File upload limits
    max_upload_size_mb: PositiveInt = Field(500, description="Maximum upload size in MB")
    max_video_duration_seconds: PositiveInt = Field(3600, description="Maximum video duration in seconds")
    max_audio_duration_seconds: PositiveInt = Field(3600, description="Maximum audio duration in seconds")
    
    # Rate limiting settings
    rate_limit_enabled: bool = Field(True, description="Enable rate limiting")
    rate_limit_default_limit: str = Field("60/minute", description="Default rate limit")
    rate_limit_auth_limit: str = Field("20/minute", description="Rate limit for authentication endpoints")
    rate_limit_transform_limit: str = Field("10/minute", description="Rate limit for transform endpoints")
    
    # Allowed file types
    allowed_video_types: list[str] = Field(
        [
            "video/mp4", 
            "video/quicktime", 
            "video/x-msvideo",
            "video/x-matroska"
        ],
        description="Allowed video MIME types"
    )
    allowed_audio_types: list[str] = Field(
        [
            "audio/mpeg", 
            "audio/mp3",
            "audio/wav", 
            "audio/x-wav",
            "audio/aac",
            "audio/flac",
            "audio/ogg"
        ],
        description="Allowed audio MIME types"
    )

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore",
        env_prefix="CLIPORA_"
    )
    
    @model_validator(mode="after")
    def _validate_s3(self) -> "Settings":
        if self.storage_type == "s3":
            missing = [k for k in ("s3_bucket_name","s3_region","aws_access_key_id","aws_secret_access_key")
                       if getattr(self, k) in (None, "",)]
            if missing:
                raise ValueError(f"S3 enabled, missing: {', '.join(missing)}")
        return self
        
    @model_validator(mode="after")
    def _validate_jwt_keys(self) -> "Settings":
        """
        Enforce strong JWT configuration depending on algorithm and environment.
        - In production with HS256: require non-empty, non-default secret.
        - In RS/ES: require existing, readable key files.
        """
        if self.algorithm == "HS256":
            if not self.secret_key:
                raise ValueError("HS256 requires secret_key")
            if self.environment == "production":
                secret_val = self.secret_key.get_secret_value() if self.secret_key else ""
                if not secret_val or secret_val == "dev-secret-key":
                    raise ValueError("In production, HS256 requires a strong non-default secret_key")
        else:
            missing = [k for k in ("jwt_private_key_path", "jwt_public_key_path") if not getattr(self, k)]
            if missing:
                raise ValueError(f"{self.algorithm} requires: {', '.join(missing)}")
            # Validate file existence & readability
            try:
                priv_path = Path(self.jwt_private_key_path)  # type: ignore[arg-type]
                pub_path = Path(self.jwt_public_key_path)  # type: ignore[arg-type]
                if not priv_path.exists() or not priv_path.is_file():
                    raise ValueError(f"Private key file not found: {priv_path}")
                if not pub_path.exists() or not pub_path.is_file():
                    raise ValueError(f"Public key file not found: {pub_path}")
                # Attempt to read to ensure readability
                _ = priv_path.read_text()
                _ = pub_path.read_text()
            except Exception as e:
                raise ValueError(f"Invalid JWT key files: {e}")
        return self
        
    @model_validator(mode="after")
    def _normalize_lists(self) -> "Settings":
        # Allow CSV in env without JSON
        def _split(v: str | list[str]) -> list[str]:
            if isinstance(v, str):
                return [s.strip() for s in v.split(",") if s.strip()]
            return v
        self.cors_origins = _split(self.cors_origins)
        self.cors_allow_methods = _split(self.cors_allow_methods)
        self.cors_allow_headers = _split(self.cors_allow_headers)
        self.trusted_hosts = _split(self.trusted_hosts)
        return self
        
    @model_validator(mode="after")
    def _defaults_for_celery(self) -> "Settings":
        if not self.celery_broker_url and self.redis_dsn:
            self.celery_broker_url = AnyUrl(str(self.redis_dsn))
        if not self.celery_result_backend and self.redis_dsn:
            self.celery_result_backend = AnyUrl(str(self.redis_dsn))
        return self

    @model_validator(mode="after")
    def _compose_postgres_dsn_from_standard_env(self) -> "Settings":
        """
        Allow non-prefixed envs (POSTGRES_*) to define the DSN when CLIPORA_ vars are not set.
        This keeps compatibility with common docker-compose/.env setups.
        """
        if not self.database_url:
            user = os.getenv("POSTGRES_USER")
            password = os.getenv("POSTGRES_PASSWORD")
            db = os.getenv("POSTGRES_DB")
            host = os.getenv("POSTGRES_HOST") or "localhost"
            port = os.getenv("POSTGRES_PORT") or "5432"
            # If user provided standard POSTGRES_* vars, compose an asyncpg DSN
            if user and password and db:
                dsn = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
                try:
                    self.postgres_dsn = PostgresDsn(dsn)
                except Exception:
                    pass
        return self
    
    @property
    def upload_dir_path(self) -> Path:
        return Path(self.upload_dir)
    
    @property
    def temp_upload_dir_path(self) -> Path:
        return Path(self.temp_upload_dir)


settings = Settings()  # type: ignore
