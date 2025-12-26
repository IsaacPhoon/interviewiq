import filetype
from fastapi import HTTPException, UploadFile, status
from filetype.types.video import Webm
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.constants import response_constants
from app.models.response import Response
from app.services.r2_storage_service import r2_storage_service


class ResponseService:
    """Service for managing interview question responses."""

    async def validate_and_upload_audio(
        self, question_id: int, audio_file: UploadFile, session: AsyncSession
    ) -> Response:
        """
        Validate and upload the audio file for a response.

        Validates the audio file format and size, uploads it to R2 storage,
        and creates a Response record in the database.
        Returns the created Response object.

        Raises:
            HTTPException: 400 if validation fails
        """
        audio_max_size_bytes = response_constants.AUDIO_MAX_SIZE_MEGABYTES * 1024 * 1024

        if audio_file.content_type not in {'audio/webm', 'video/webm'}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Audio file must be in webm format.',
            )

        if audio_file.size is not None and audio_file.size > audio_max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(f'Audio file size must be less than {response_constants.AUDIO_MAX_SIZE_MEGABYTES} MB.'),
            )

        file_header = await audio_file.read(261)

        if not file_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Audio file is empty.',
            )

        file_type = filetype.guess(file_header)
        if not isinstance(file_type, Webm):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Audio file must be in webm format.',
            )

        total_size = len(file_header)
        while chunk := await audio_file.read(1024 * 1024):
            total_size += len(chunk)
            if total_size > audio_max_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(f'Audio file size must be less than {response_constants.AUDIO_MAX_SIZE_MEGABYTES} MB.'),
                )

        await audio_file.seek(0)

        try:
            audio_path = await r2_storage_service.upload_audio(audio_file.file)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='An unexpected error occurred while uploading the audio file.',
            ) from e

        response = Response(
            audio_path=audio_path,
            question_id=question_id,
        )

        session.add(response)
        await session.commit()
        await session.refresh(response)

        return response


response_service = ResponseService()
