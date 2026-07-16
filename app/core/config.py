from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/secureslot"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-this-in-your-real-.env-file"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

settings = Settings()