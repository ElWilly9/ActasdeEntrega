from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./inventario.db"
    SECRET_KEY: str = "default-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def force_pg8000_driver(cls, v: str) -> str:
        if v and v.startswith("postgresql://") and "+pg8000" not in v:
            return v.replace("postgresql://", "postgresql+pg8000://", 1)
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
