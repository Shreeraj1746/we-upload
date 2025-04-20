"""Application configuration settings module."""

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    This class uses Pydantic's BaseSettings which loads environment variables
    prefixed with 'WE_UPLOAD_'.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="WE_UPLOAD_"
    )

    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "We-Upload"
    DEBUG: bool = False

    # CORS settings
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        """Parse CORS origins from string.

        Args:
            v: The value to be validated.

        Returns:
            List of CORS origins or the original value if it's already a list.
        """
        try:
            if isinstance(v, str) and not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            elif isinstance(v, list | str):
                return v
        except Exception:
            raise ValueError(v)

    # Database settings
    POSTGRES_SERVER: str = "db"  # Default to docker-compose service name
    POSTGRES_USER: str = "postgres"  # Default values
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "we_upload"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(
        cls,
        v: PostgresDsn | str | None,
    ) -> PostgresDsn | str | None:
        """Assemble the database connection URI.

        Args:
            v: The value to be validated.

        Returns:
            Assembled PostgreSQL database URI.
        """
        if isinstance(v, str):
            return v

        # Return hardcoded connection string for local development
        return "postgresql://postgres:postgres@db:5432/we_upload"

    # JWT settings
    SECRET_KEY: str = "supersecretkey"  # Default value for development
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # AWS settings
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "minio"  # Default for local MinIO
    AWS_SECRET_ACCESS_KEY: str = "minio123"  # Default for local MinIO
    S3_BUCKET_NAME: str = "we-upload-local"  # Default bucket name
    PRESIGNED_URL_EXPIRY: int = 3600  # 1 hour

    # User settings
    FIRST_SUPERUSER: str | None = None
    FIRST_SUPERUSER_PASSWORD: str | None = None


# Create a global settings instance
settings = Settings()
