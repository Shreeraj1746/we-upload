"""Application configuration settings module."""

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    This class uses Pydantic's BaseSettings which loads environment variables
    prefixed with 'WE_UPLOAD_'.
    """

    # Configure Pydantic settings to load environment variables from a .env file,
    # using the "WE_UPLOAD_" prefix to avoid conflicts and group related variables.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="WE_UPLOAD_"
    )

    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "We-Upload"
    DEBUG: bool = False

    # CORS settings
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "weuploadadmin"
    POSTGRES_PASSWORD: str = "Password123!"
    POSTGRES_DB: str = "weupload"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: str = (
        "postgresql://weuploadadmin:Password123!@localhost:5432/weupload"
    )

    # JWT settings
    SECRET_KEY: str = "supersecretkey"  # Default value for development
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # AWS settings
    AWS_REGION: str = "ap-south-1"  # Default to ap-south-1 for all environments
    AWS_ACCESS_KEY_ID: str = "minio"  # Default for local MinIO
    AWS_SECRET_ACCESS_KEY: str = "minio123"  # Default for local MinIO
    S3_BUCKET_NAME: str = "we-upload-local"  # Default bucket name
    PRESIGNED_URL_EXPIRY: int = 3600  # 1 hour
    # Set to true to use EC2 instance role instead of access keys in production
    USE_INSTANCE_ROLE: bool = True

    # User settings
    FIRST_SUPERUSER: str | None = None
    FIRST_SUPERUSER_PASSWORD: str | None = None


# Create settings instance
settings = Settings()
