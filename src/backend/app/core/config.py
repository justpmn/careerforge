
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CareerForge API"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = (
        "postgresql+psycopg://careerforge:careerforge@localhost:5432/careerforge"
    )

    jwt_secret_key: str | None = None
    jwt_access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
