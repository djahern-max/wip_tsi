from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import validator
from decouple import config


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = config("APP_NAME", default="TSI WIP Reporting Tool")
    APP_VERSION: str = config("APP_VERSION", default="1.0.0")
    DEBUG: bool = config("DEBUG", default=True, cast=bool)
    SECRET_KEY: str = config("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config(
        "ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int
    )

    # Database Settings
    DATABASE_URL: str = config("DATABASE_URL")
    DATABASE_HOST: str = config("DATABASE_HOST", default="localhost")
    DATABASE_PORT: int = config("DATABASE_PORT", default=5432, cast=int)
    DATABASE_NAME: str = config("DATABASE_NAME")
    DATABASE_USER: str = config("DATABASE_USER")
    DATABASE_PASSWORD: str = config("DATABASE_PASSWORD")

    # Redis Settings
    REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379")

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Logging
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
