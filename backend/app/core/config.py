from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

dotenv_path = Path(__file__).parent.parent.parent / '.env'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=dotenv_path,
        env_ignore_empty=True,
        extra='ignore',
    )

    database_url: str
    clerk_jwks_url: str
    clerk_webhook_secret: str


settings = Settings()  # type: ignore[call-arg]
