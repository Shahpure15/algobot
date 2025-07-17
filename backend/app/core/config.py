import os
import secrets
from typing import Literal, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    """Application settings loaded from environment variables"""
    # Environment
    environment: Literal["development", "production", "test"] = Field(
        default=os.getenv("ENVIRONMENT", "development")
    )
    debug: bool = Field(default=os.getenv("DEBUG", "true").lower() == "true")
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "info").lower())
    
    # Database
    database_url: str = Field(
        default=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@database:5432/algobot")
    )
    
    # Security
    secret_key: str = Field(
        default=os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    )
    jwt_secret: str = Field(
        default=os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_days: int = Field(default=30)
    
    # CORS
    cors_origins: List[str] = Field(
        default=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    )

    # API Credentials
    delta_api_key: str = Field(default=os.getenv("DELTA_API_KEY", ""))
    delta_api_secret: str = Field(default=os.getenv("DELTA_API_SECRET", ""))
    delta_base_url: str = Field(default=os.getenv("DELTA_BASE_URL", "https://api.delta.exchange"))
    
    # API Configurations
    apis: List[str] = Field(default=[])
    api_prefix: str = Field(default="/api")


# Create settings instance
settings = Settings()