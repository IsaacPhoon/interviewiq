from datetime import UTC, datetime
from typing import Annotated

from fastapi import BackgroundTasks, Depends
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import engine
from app.models.enums import ResponseProcessingStatus
from app.models.question import Question
from app.models.response import Response
from app.services.claude_service import ClaudeServiceError, claude_service
from app.services.r2_storage_service import R2ServiceError, r2_storage_service
from app.services.transcription_service import TranscriptionServiceError, transcription_service


class ResponseProcessingService:
    """Service for processing responses to interview questions in the background using FastAPI's BackgroundTasks."""

    @classmethod
    def create_service_instance(cls, background_tasks: BackgroundTasks) -> ResponseProcessingService:
        """
        Factory method to create an instance of ResponseProcessingService with BackgroundTasks.

        Used as a callable dependency in FastAPI routes.
        """
        return cls(background_tasks)

    def __init__(self, background_tasks: BackgroundTasks):
        """Initialize the ResponseProcessingService with FastAPI's BackgroundTasks."""
        self._background_tasks = background_tasks

    def enqueue_response_processing(self, response_id: int) -> None:
        """
        Enqueue background tasks for processing a response.

        Adds the response processing task to FastAPI's BackgroundTasks to be executed after the endpoint returns.
        """
        self._background_tasks.add_task(self._process_response, response_id=response_id)

    async def _process_response(self, response_id: int) -> None:
        """
        Process the response with the given ID.

        Processing includes transcribing the audio and evaluating the response.
        Handles errors at each step and updates the response status accordingly.
        Execution halts early upon encountering an error.
        """
        async with AsyncSession(engine) as session:
            try:
                result = await session.exec(
                    select(Response)
                    .where(Response.id == response_id)
                    .options(selectinload(Response.question).selectinload(Question.job_description))  # type: ignore
                )
                response = result.one_or_none()
                if response is None:
                    return

                response.processing_started_at = datetime.now(UTC)
                session.add(response)
                await session.commit()
                await session.refresh(response)

                try:
                    await self._transcribe_response(session=session, response=response)
                except R2ServiceError as e:
                    await self._mark_as_failed(
                        session=session,
                        response=response,
                        message=f'Audio retrieval failed before transcription: {str(e)}',
                    )
                    return
                except TranscriptionServiceError as e:
                    await self._mark_as_failed(
                        session=session,
                        response=response,
                        message=f'Transcription failed: {str(e)}',
                    )
                    return

                try:
                    await self._evaluate_response(session=session, response=response)
                except ClaudeServiceError as e:
                    await self._mark_as_failed(
                        session=session, response=response, message=f'Evaluation failed: {str(e)}'
                    )
                    return

            except Exception as e:
                if isinstance(response, Response):
                    await self._mark_as_failed(
                        session=session,
                        response=response,
                        message=f'Unexpected error during processing: {type(e).__name__}: {str(e)}',
                    )
                return

    async def _transcribe_response(self, session: AsyncSession, response: Response) -> None:
        """
        Transcribe the audio file for the response.

        Calls the transcription service to transcribe the audio and
        updates the response database record with the transcript and status.
        Lets exceptions propagate to the caller for handling.
        """
        response.status = ResponseProcessingStatus.TRANSCRIBING
        session.add(response)
        await session.commit()
        await session.refresh(response)

        presigned_audio_url = await r2_storage_service.get_audio_url(response.audio_path)
        transcript = await transcription_service.transcribe_audio(presigned_audio_url)

        response.transcript = transcript
        response.status = ResponseProcessingStatus.TRANSCRIBED
        session.add(response)
        await session.commit()
        await session.refresh(response)

    async def _evaluate_response(self, session: AsyncSession, response: Response) -> None:
        """
        Evaluate the transcribed response using the Claude service.

        Calls the Claude service to evaluate the transcript and
        updates the response database record with the evaluation results and status.
        Lets exceptions propagate to the caller for handling.
        """
        if response.transcript is None:
            raise RuntimeError('Evaluation called on response with no transcript.')

        response.status = ResponseProcessingStatus.EVALUATING
        session.add(response)
        await session.commit()
        await session.refresh(response)

        question = response.question
        job_description = question.job_description

        evaluation = await claude_service.evaluate_response(
            job_description_text=job_description.description_text,
            company_name=job_description.company_name,
            job_title=job_description.job_title,
            question_text=question.question_text,
            transcript=response.transcript,
        )

        response.evaluation_obj = evaluation
        response.status = ResponseProcessingStatus.EVALUATED
        response.processing_completed_at = datetime.now(UTC)
        session.add(response)
        await session.commit()
        await session.refresh(response)

    async def _mark_as_failed(self, session: AsyncSession, response: Response, message: str) -> None:
        """
        Mark the response evaluation as failed with the given error message.

        Updates the response database record with the error message and status.
        """
        response.status = ResponseProcessingStatus.ERROR
        response.error_message = message
        response.processing_completed_at = datetime.now(UTC)
        session.add(response)
        await session.commit()
        await session.refresh(response)


ResponseProcessingServiceDep = Annotated[
    ResponseProcessingService, Depends(ResponseProcessingService.create_service_instance)
]
