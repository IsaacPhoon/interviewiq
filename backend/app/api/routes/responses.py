from fastapi import APIRouter, UploadFile, status

from app.core.auth import CurrentUserDep
from app.core.database import SessionDep

router = APIRouter(tags=['Responses'])


@router.post(
    path='/questions/{question_id}/responses',
    status_code=status.HTTP_201_CREATED,
    response_model=None,  # Replace with actual response model
)
async def sumbit_response(
    question_id: int,
    audio_file: UploadFile,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Submit an audio response to a question, transcribe it, and get evaluation results.

    ADD DOCSTRING DETAILS HERE
    """
    # Implementation goes here
    pass


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
