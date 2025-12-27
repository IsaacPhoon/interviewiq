from fastapi import APIRouter, UploadFile, status

from app.core.auth import CurrentUserDep
from app.core.database import SessionDep
from app.models.response import ResponseInitialResponse, ResponseListItem, ResponsePollingResponse
from app.services.question_service import question_service
from app.services.r2_storage_service import r2_storage_service
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

    Returns 404 if question not found or not owned by user.
    Returns 400 if audio file is an invalid format or exceeds size limit.
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
    path='/responses/{response_id}/status',
    response_model=ResponsePollingResponse,
    response_model_exclude_unset=True,
)
async def get_response(
    response_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Retrieve a response's processing status and results (if available).

    Polling endpoint to check the status of a response.
    Returns progressive disclosure of fields as processing advances and/or completes.

    Returns 404 if response not found or not owned by user.
    """
    response = await response_service.get_user_response(
        response_id=response_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    polling_response = await response_service.get_polling_response(response)

    return polling_response


@router.get(
    path='/questions/{question_id}/responses',
    response_model=list[ResponseListItem],
)
async def get_responses(
    question_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Retrieve all responses for a specific question.

    Returns a list of fully processed responses associated with the given question ID.

    Returns 404 if question not found or not owned by user.
    """
    responses = await response_service.get_question_responses(
        question_id=question_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    response_list = []
    for response in responses:
        audio_url = await r2_storage_service.get_audio_url(response.audio_path)
        response_dict = response.model_dump()
        response_dict['audio_url'] = audio_url
        response_item = ResponseListItem.model_validate(response_dict)
        response_list.append(response_item)

    return response_list


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
