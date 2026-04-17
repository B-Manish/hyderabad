from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Hyderabad Road Reporting Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://hyderabad:hyderabad@localhost:5432/hyderabad_roads"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO / S3
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "road-reports"
    S3_PRESIGNED_EXPIRY: int = 300  # seconds
    S3_PUBLIC_URL: str = "http://localhost:9000"

    # Auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60 * 24  # 24 hours

    # Rate Limiting
    RATE_LIMIT_REPORTS_PER_HOUR: int = 10
    MAX_REPORTS_PER_USER_PER_DAY: int = 30
    MAX_SUPPORTS_PER_USER_PER_DAY: int = 50

    # Phase 5: Configurable Thresholds
    DUPLICATE_RADIUS_METERS: int = 30
    VERIFICATION_THRESHOLD: float = 0.6
    FIXED_CONFIRM_THRESHOLD: int = 3

    # Upload Constraints
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MIN_IMAGE_WIDTH: int = 640
    MIN_IMAGE_HEIGHT: int = 480
    ALLOWED_CONTENT_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]
    MAX_MEDIA_PER_REPORT: int = 5

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
