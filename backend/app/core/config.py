from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

dotenv_path = Path(__file__).parent.parent.parent / '.env'


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=dotenv_path,
        env_ignore_empty=True,
        extra='ignore',
    )

    DATABASE_URL: str

    CLERK_JWKS_URL: str
    CLERK_WEBHOOK_SECRET: str

    AZURE_OPENAI_BASE_URL: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_MODEL: str

    R2_ENDPOINT_URL: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str

    AZURE_SPEECH_ENDPOINT: str
    AZURE_SPEECH_KEY: str
    AZURE_SPEECH_API_VERSION: str


settings = Settings()  # type: ignore[call-arg]
