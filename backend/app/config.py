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
    database_url: str = "sqlite:///./MediShield_db.db"

    # --- JWT Auth ---
    jwt_secret_key: str = Field(..., validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

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

    # --- Mailtrap / Email ---
    mailtrap_host: str = Field(..., validation_alias="MAILTRAP_HOST")
    mailtrap_port: int =  Field(..., validation_alias="MAILTRAP_PORT")
    mailtrap_user: str = Field(..., validation_alias="MAILTRAP_USER")
    mailtrap_password: str = Field(..., validation_alias="MAILTRAP_PASSWORD")

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