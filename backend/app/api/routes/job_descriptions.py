from fastapi import APIRouter, HTTPException, status

from app.core.auth import CurrentUserDep
from app.core.database import SessionDep
from app.models.job_description import (
    JobDescription,
    JobDescriptionCreate,
    JobDescriptionResponse,
    StatusEnum,
)
from app.models.question import Question
from app.services.claude import claude_service

router = APIRouter(prefix='/job-description', tags=['Job Descriptions'])


@router.post(
    '/', status_code=status.HTTP_201_CREATED, response_model=JobDescriptionResponse
)
async def create_job_description(
    job_description: JobDescriptionCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    try:
        db_job_description = JobDescription.model_validate(
            job_description, update={'user_id': current_user.id}
        )
        session.add(db_job_description)
        await session.commit()
        await session.refresh(db_job_description)

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create job description.',
        )

    try:
        questions_list = await claude_service.generate_question(
            job_description_text=db_job_description.description_text,
            company_name=db_job_description.company_name,
            job_title=db_job_description.job_title,
        )

        for question_text in questions_list:
            question = Question(
                question_text=question_text,
                job_description_id=db_job_description.id,  # type: ignore[arg-type]
            )
            session.add(question)

        db_job_description.status = StatusEnum.QUESTIONS_GENERATED
        session.add(db_job_description)
        await session.commit()
        await session.refresh(db_job_description)

    except Exception as e:
        await session.rollback()
        db_job_description.status = StatusEnum.ERROR
        db_job_description.error_message = str(e)
        session.add(db_job_description)
        await session.commit()
        await session.refresh(db_job_description)

    return db_job_description
