import uuid
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client
from starlette.concurrency import run_in_threadpool
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    stop_any,
    wait_exponential_jitter,
)

from app.core.config import settings


class R2ServiceError(Exception):
    """Raised when there is an error interacting with Cloudflare R2 through boto3."""


class R2StorageService:
    """Service for interacting with Cloudflare R2 storage."""

    def __init__(self):
        """Initialize the R2StorageService instance."""
        self._bucket_name = settings.R2_BUCKET_NAME
        self._r2_client: S3Client | None = None

    def start(self):
        """Start the service by initializing the boto3 R2 client."""
        self._r2_client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name='auto',
        )

    def stop(self):
        """Close the service's boto3 R2 client."""
        if self._r2_client is not None:
            self._r2_client.close()

    def _ensure_started(self) -> S3Client:
        """
        Ensure the service has been started and return the non-None client.

        Raises:
            R2ServiceError: If the service has not been started
        """
        if self._r2_client is None:
            raise R2ServiceError('R2StorageService has not been started. Call start() before using the service.')
        return self._r2_client

    @retry(
        stop=stop_any(stop_after_attempt(5), stop_after_delay(15)),
        wait=wait_exponential_jitter(initial=1, max=10, jitter=1),
        retry=retry_if_exception_type(R2ServiceError),
        reraise=True,
    )
    async def upload_audio(self, audio_file: BinaryIO) -> str:
        """
        Upload an audio file to R2 storage and return its path.

        Accepts a binary file-like object and uploads it to the configured R2 bucket.
        Generates a unique path for the file using UUIDv7, under the 'audio/' directory.

        Raises:
            R2ServiceError: If the upload fails
        """
        client = self._ensure_started()
        audio_path = f'audio/{uuid.uuid7()}.webm'
        try:
            await run_in_threadpool(
                client.upload_fileobj,
                Fileobj=audio_file,
                Bucket=self._bucket_name,
                Key=audio_path,
                ExtraArgs={'ContentType': 'audio/webm'},
            )
            return audio_path
        except ClientError as e:
            raise R2ServiceError(f'Failed to upload audio to R2 storage: {str(e)}') from e

    @retry(
        stop=stop_any(stop_after_attempt(3), stop_after_delay(10)),
        wait=wait_exponential_jitter(initial=1, max=10, jitter=1),
        retry=retry_if_exception_type(R2ServiceError),
        reraise=True,
    )
    async def get_audio_url(self, audio_path: str) -> str:
        """
        Generate a presigned URL for accessing an audio file in R2 storage.

        Accepts the path of the audio file in R2 and returns a presigned URL
        that is valid for 1 hour.

        Raises:
            R2ServiceError: If URL generation fails
        """
        client = self._ensure_started()
        try:
            url = await run_in_threadpool(
                client.generate_presigned_url,
                'get_object',
                Params={'Bucket': self._bucket_name, 'Key': audio_path},
                ExpiresIn=3600,
            )
            return url
        except ClientError as e:
            raise R2ServiceError(f'Failed to generate presigned URL: {str(e)}') from e


r2_storage_service = R2StorageService()
