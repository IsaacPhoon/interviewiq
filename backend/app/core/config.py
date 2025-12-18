from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

dotenv_path = Path(__file__).parent.parent.parent / '.env'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=dotenv_path,
        env_ignore_empty=True,
        extra='ignore',
    )

    DATABASE_URL: str
    CLERK_JWKS_URL: str
    CLERK_WEBHOOK_SECRET: str


settings = Settings()  # type: ignore[call-arg]
