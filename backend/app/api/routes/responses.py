from fastapi import APIRouter, UploadFile, status

from app.core.auth import CurrentUserDep
from app.core.database import SessionDep
from app.models.response import ResponseInitialResponse
from app.services.question_service import question_service
from app.services.response_processing_service import ResponseProcessingServiceDep
from app.services.response_service import response_service

router = APIRouter(tags=['Responses'])


@router.post(
    path='/questions/{question_id}/responses',
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseInitialResponse,
)
async def sumbit_response(
    question_id: int,
    audio_file: UploadFile,
    current_user: CurrentUserDep,
    session: SessionDep,
    response_processing_service: ResponseProcessingServiceDep,
):
    """
    Submit an audio response to a question and enqueue it for processing.

    Validates the question ownership and audio file, uploads the audio to R2 storage,
    creates a Response record in the database, and enqueues background task for transcription and evaluation.
    Returns the initial response details including ID, status, creation timestamp, and a confirmation message.
    Use the polling endpoint to check processing status and retrieve results later.
    """
    await question_service.get_user_question(
        question_id=question_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    response = await response_service.validate_and_upload_audio(
        question_id=question_id, audio_file=audio_file, session=session
    )

    response_processing_service.enqueue_response_processing(response.id)  # type: ignore[arg-type]

    return response


@router.get(
    path='/questions/{question_id}/responses',
    response_model=list,  # Replace with actual response model
)
async def get_responses(
    question_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Retrieve all responses for a specific question.

    ADD DOCSTRING DETAILS HERE
    """
    # Implementation goes here
    pass


@router.get(
    path='/responses/{response_id}',
    response_model=None,  # Replace with actual response model
)
async def get_response(
    response_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Retrieve a specific response by its ID.

    ADD DOCSTRING DETAILS HERE
    """
    # Implementation goes here
    pass


@router.get(
    path='/responses/{response_id}/audio',
    response_model=None,  # Replace with actual response model
)
async def get_response_audio(
    response_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Retrieve the audio file URL for a specific response.

    ADD DOCSTRING DETAILS HERE
    """
    # Implementation goes here
    pass


@router.delete(
    path='/responses/{response_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_response(
    response_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Delete a specific response by its ID.

    ADD DOCSTRING DETAILS HERE
    """
    # Implementation goes here
    pass
