from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

dotenv_path = Path(__file__).parent.parent.parent / '.env'


class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=dotenv_path,
        env_ignore_empty=True,
        extra='ignore',
    )


settings = Settings()  # type: ignore[call-arg]
