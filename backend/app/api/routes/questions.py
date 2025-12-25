from fastapi import APIRouter

from app.core.auth import CurrentUserDep
from app.core.database import SessionDep
from app.models.question import QuestionResponse
from app.services.question_service import question_service

router = APIRouter(tags=['Questions'])


@router.get(
    path='/job-descriptions/{job_description_id}/questions',
    response_model=list[QuestionResponse],
)
async def get_questions(
    job_description_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Retrieve all interview questions for a specific job description.

    Returns a list of questions associated with the given job description ID.

    Returns 404 if job description not found or not owned by user.
    """
    questions = await question_service.get_job_description_questions(
        job_description_id=job_description_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    question_list = []
    for question in questions:
        question_item = await QuestionResponse.from_question(question=question, session=session)
        question_list.append(question_item)

    return question_list


@router.get(
    path='/questions/{question_id}',
    response_model=QuestionResponse,
)
async def get_question(
    question_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Retrieve a specific interview question by ID.

    Returns the question details including attempt count.

    Returns 404 if not found or not owned by user.
    """
    question = await question_service.get_user_question(
        question_id=question_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    return await QuestionResponse.from_question(question=question, session=session)
