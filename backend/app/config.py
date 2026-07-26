"""Central application configuration loaded from environment variables."""

from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import base64


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "MediShield"

    environment: Literal[
        "development",
        "testing",
        "staging",
        "production",
    ] = "development"

    # --- Database ---
    # Async driver, used by the running app (SQLAlchemy async engine).
    #   SQLite : sqlite+aiosqlite:///./MediShield_db.db
    #   MySQL  : mysql+aiomysql://user:password@localhost:3306/medishield_db
    database_url: str = Field(..., validation_alias="DATABASE_URL")

    # --- JWT Auth ---
    jwt_secret_key: str = Field(..., validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=480, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # --- AES-256-GCM Encryption ---
    encryption_key: str = Field(..., validation_alias="ENCRYPTION_KEY")

    # --- CORS ---
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    # --- Dengue Risk Thresholds ---
    risk_threshold_medium: float = 10
    risk_threshold_high: float = 50
    risk_threshold_very_high: float = 150

    # --- Email / SMTP ---
    smtp_host: str = Field(default="localhost", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, validation_alias="SMTP_PORT")
    smtp_user: str = Field(default="", validation_alias="SMTP_USER")
    smtp_password: str = Field(default="", validation_alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=False, validation_alias="SMTP_USE_TLS")

    # --- OTP / Security ---
    otp_expire_minutes: int = Field(default=15, validation_alias="OTP_EXPIRE_MINUTES")
    otp_max_attempts: int = Field(default=5, validation_alias="OTP_MAX_ATTEMPTS")
    otp_resend_cooldown_seconds: int = Field(default=60, validation_alias="OTP_RESEND_COOLDOWN_SECONDS")

    # Account lockout: after this many failed login attempts (password or
    # first-login OTP) within the window, further attempts are rejected
    # until enough of them age out of the sliding window — see
    # AuthService._enforce_not_locked.
    login_max_failed_attempts: int = Field(default=10, validation_alias="LOGIN_MAX_FAILED_ATTEMPTS")
    login_lockout_window_minutes: int = Field(default=15, validation_alias="LOGIN_LOCKOUT_WINDOW_MINUTES")

    # --- Logging ---
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # --- Appointments ---
    # Spec doesn't state a slot length; this is how long a booked
    # appointment blocks the doctor when checking for overlaps.
    appointment_slot_minutes: int = Field(default=30, validation_alias="APPOINTMENT_SLOT_MINUTES")

    # --- Documents (Module 12) ---
    upload_dir: str = Field(default="uploads", validation_alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=10, validation_alias="MAX_UPLOAD_SIZE_MB")

    @property
    def sync_database_url(self) -> str:
        """A synchronous-driver equivalent of database_url, used only by
        Alembic (migrations run sync even when the app runtime is async)."""
        return (
            self.database_url
            .replace("sqlite+aiosqlite://", "sqlite://")
            .replace("mysql+aiomysql://", "mysql+pymysql://")
        )

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, value: str) -> str:
        try:
            decoded = base64.urlsafe_b64decode(value)
        except Exception:
            raise ValueError(
                "ENCRYPTION_KEY must be a valid urlsafe base64 string"
            )

        if len(decoded) != 32:
            raise ValueError(
                "ENCRYPTION_KEY must decode to exactly 32 bytes"
            )

        return value


settings = Settings()