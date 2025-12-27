import filetype
from fastapi import HTTPException, UploadFile, status
from filetype.types.video import Webm
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.constants import response_constants
from app.models.enums import ResponseProcessingStatus
from app.models.job_description import JobDescription
from app.models.question import Question
from app.models.response import Response, ResponsePollingResponse
from app.services.r2_storage_service import r2_storage_service


class ResponseService:
    """Service for managing interview question responses."""

    async def get_user_response(
        self,
        response_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> Response:
        """
        Get a response and verify the user owns it.

        Performs ownership verification to ensure users can only access
        their own responses.

        Raises:
            HTTPException: 404 if response not found or user doesn't own it
        """
        stmt = (
            select(Response)
            .join(Question, col(Response.question_id) == col(Question.id))
            .join(JobDescription, col(Question.job_description_id) == col(JobDescription.id))
            .where(Response.id == response_id, JobDescription.user_id == user_id)
        )
        result = await session.exec(stmt)
        response = result.one_or_none()

        if response is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Response not found',
            )

        return response

    async def get_question_responses(
        self,
        question_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> list[Response]:
        """
        Get all responses for a question with ownership verification.

        Raises:
            HTTPException: 404 if question not found or user doesn't own it
        """
        question_stmt = (
            select(Question).join(JobDescription).where(Question.id == question_id, JobDescription.user_id == user_id)
        )
        question_result = await session.exec(question_stmt)
        if question_result.one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Question not found',
            )

        responses_stmt = select(Response).where(Response.question_id == question_id)
        responses_result = await session.exec(responses_stmt)
        return list(responses_result.all())

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

    async def get_polling_response(self, response: Response) -> ResponsePollingResponse:
        """
        Construct a ResponsePollingResponse from a Response model.

        Provides progressive disclosure of fields based on the current processing status.

        Raises:
            RuntimeError: if expected fields are missing for the current status
        """
        audio_url = await r2_storage_service.get_audio_url(response.audio_path)

        polling_response_dict = {
            'id': response.id,
            'status': response.status,
            'created_at': response.created_at,
            'message': '',
            'audio_url': audio_url,
        }

        if response.status == ResponseProcessingStatus.PENDING:
            polling_response_dict['message'] = 'Response is pending processing.'

        elif response.status == ResponseProcessingStatus.TRANSCRIBING:
            polling_response_dict['message'] = 'Response is being transcribed.'

        elif response.status == ResponseProcessingStatus.TRANSCRIBED:
            polling_response_dict['message'] = 'Response has been transcribed and is awaiting evaluation.'
            if response.transcript is None:
                raise RuntimeError('Response is transcribed but transcript is None.')
            polling_response_dict['transcript'] = response.transcript

        elif response.status == ResponseProcessingStatus.EVALUATING:
            polling_response_dict['message'] = 'Response has been transcribed and is being evaluated.'
            if response.transcript is None:
                raise RuntimeError('Response is evaluating but transcript is None.')
            polling_response_dict['transcript'] = response.transcript

        elif response.status == ResponseProcessingStatus.EVALUATED:
            polling_response_dict['message'] = 'Response has been evaluated.'
            if response.transcript is None:
                raise RuntimeError('Response is evaluated but transcript is None.')
            polling_response_dict['transcript'] = response.transcript
            if response.evaluation_obj is None:
                raise RuntimeError('Response is evaluated but evaluation is None.')
            polling_response_dict['evaluation'] = response.evaluation_obj

        else:
            polling_response_dict['message'] = 'An error occurred during processing. Please contact support.'

        polling_response = ResponsePollingResponse.model_validate(polling_response_dict)

        return polling_response


response_service = ResponseService()
