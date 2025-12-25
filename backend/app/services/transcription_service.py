from typing import Literal

import httpx
from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    stop_any,
    wait_exponential_jitter,
)

from app.core.config import settings


class TranscriptionServiceError(Exception):
    """Raised when there is an error during transcription process."""


class TranscriptionDefinition(BaseModel):
    """Definition for transcription request to Azure Speech-to-Text API."""

    audioUrl: HttpUrl
    locales: list[str] = ['en-US']
    profanityFilterMode: Literal['None', 'Masked', 'Removed', 'Tags'] = 'None'


class CombinedPhrase(BaseModel):
    """
    Represents the full transcript text for a channel in Azure
    Speech-to-Text response.
    """

    text: str
    channel: int | None = None

    @field_validator('text', mode='after')
    @classmethod
    def check_for_empty_text(cls, value: str) -> str:
        if not value.strip():
            return 'No speech detected in audio.'
        return value


class AzureTranscriptionResponse(BaseModel):
    """Model for validating Azure Speech-to-Text transcription response."""

    combinedPhrases: list[CombinedPhrase] = Field(min_length=1)


class TranscriptionService:
    """Service for handling speech-to-text transcription operations."""

    def __init__(self):
        """Initialize the TranscriptionService with HTTPX async client."""
        base_url = settings.AZURE_SPEECH_ENDPOINT.rstrip('/')
        transcription_url = f'{base_url}/speechtotext/transcriptions:transcribe'
        self.client = httpx.AsyncClient(
            http2=True,
            timeout=httpx.Timeout(connect=5.0, read=75.0, write=5.0, pool=10.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            base_url=transcription_url,
            params={
                'api-version': settings.AZURE_SPEECH_API_VERSION,
            },
            headers={
                'Accept': 'application/json',
                'Ocp-Apim-Subscription-Key': settings.AZURE_SPEECH_KEY,
            },
        )


    @retry(
        stop=stop_any(stop_after_attempt(3), stop_after_delay(120)),
        wait=wait_exponential_jitter(initial=2, max=10, jitter=1),
        retry=retry_if_exception_type(TranscriptionServiceError),
        reraise=True,
    )
    async def transcribe_audio(self, audio_url: str) -> str:
        """
        Transcribe audio from the given public audio URL using Azure Speech-to-Text API.

        Returns the full transcript text from all channels combined.

        Raises:
            TranscriptionServiceError: If transcription fails or response is invalid
        """
        try:
            definition = TranscriptionDefinition(audioUrl=audio_url)  # type: ignore[arg-type]

            response = await self.client.post(
                url='',
                files={
                    'definition': (
                        None,
                        definition.model_dump_json(),
                        'application/json',
                    ),
                },
            )
            response.raise_for_status()

            result = AzureTranscriptionResponse.model_validate_json(response.content)

            transcript = result.combinedPhrases[0].text
            return transcript
        except httpx.HTTPStatusError as e:
            raise TranscriptionServiceError(
                f'Azure Speech API request failed: {str(e)}. Status code: {e.response.status_code}'
            ) from e
        except httpx.RequestError as e:
            raise TranscriptionServiceError(f'Failed to connect to Azure Speech API: {str(e)}') from e
        except ValidationError as e:
            raise TranscriptionServiceError(f'Failed to validate Azure Speech API response: {str(e)}') from e
        except Exception as e:
            raise TranscriptionServiceError(
                f'Unexpected error during transcription. {type(e).__name__}: {str(e)}'
            ) from e
