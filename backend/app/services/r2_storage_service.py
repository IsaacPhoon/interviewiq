import asyncio
import uuid
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class R2ServiceError(Exception):
    """Raised when there is an error interacting with Cloudflare R2 through boto3."""


class R2StorageService:
    """Service for interacting with Cloudflare R2 storage."""

    def __init__(self):
        """Initialize the R2StorageService with boto3 client and bucket settings."""
        self.bucket_name = settings.R2_BUCKET_NAME
        self.r2_client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name='auto',
        )

    async def upload_audio(self, audio_file: BinaryIO) -> str:
        """
        Upload an audio file to R2 storage and return its path.

        Accepts a binary file-like object and uploads it to the configured R2 bucket.
        Generates a unique path for the file using UUIDv7, under the 'audio/' directory.

        Raises:
            R2ServiceError: If the upload fails
        """
        audio_path = f'audio/{uuid.uuid7()}.webm'
        try:
            await asyncio.to_thread(
                self.r2_client.upload_fileobj,
                Fileobj=audio_file,
                Bucket=self.bucket_name,
                Key=audio_path,
                ExtraArgs={'ContentType': 'audio/webm'},
            )
            return audio_path
        except ClientError as e:
            raise R2ServiceError(f'Failed to upload audio to R2 storage: {e}') from e

    async def get_audio_url(self, audio_path: str) -> str:
        """
        Generate a presigned URL for accessing an audio file in R2 storage.

        Accepts the path of the audio file in R2 and returns a presigned URL
        that is valid for 1 hour.

        Raises:
            R2ServiceError: If URL generation fails
        """
        try:
            url = await asyncio.to_thread(
                self.r2_client.generate_presigned_url,
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': audio_path},
                ExpiresIn=3600,
            )
            return url
        except ClientError as e:
            raise R2ServiceError(f'Failed to generate presigned URL: {e}') from e


r2_storage_service = R2StorageService()
