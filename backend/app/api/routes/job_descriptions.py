from fastapi import APIRouter, status
from sqlmodel import col, select

from app.core.auth import CurrentUserDep
from app.core.database import SessionDep
from app.models.job_description import (
    JobDescription,
    JobDescriptionCreate,
    JobDescriptionListResponse,
    JobDescriptionResponse,
)
from app.services.job_description_service import job_description_service

router = APIRouter(prefix='/job-description', tags=['Job Descriptions'])


@router.post(
    '/', status_code=status.HTTP_201_CREATED, response_model=JobDescriptionResponse
)
async def create_job_description(
    job_description: JobDescriptionCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    db_job_description = JobDescription.model_validate(
        job_description, update={'user_id': current_user.id}
    )
    result = await job_description_service.create_entry_and_generate_questions(
        job_description=db_job_description, session=session
    )
    return result


@router.get('/', response_model=list[JobDescriptionListResponse])
async def get_job_descriptions(
    current_user: CurrentUserDep, session: SessionDep, limit: int = 10, offset: int = 0
):
    stmt = (
        select(JobDescription)
        .where(JobDescription.user_id == current_user.id)
        .order_by(col(JobDescription.created_at).desc())
    )
    result = await session.exec(stmt)
    job_descriptions = result.all()

    job_description_list = []
    for jd in job_descriptions:
        (
            questions_with_responses,
            total_questions,
        ) = await job_description_service.count_questions_with_responses(
            job_description_id=jd.id,  # type: ignore[arg-type]
            session=session,
        )
        jd_item = JobDescriptionListResponse(
            id=jd.id,  # type: ignore[arg-type]
            description_text=jd.description_text,
            status=jd.status,
            created_at=jd.created_at,
            total_questions=total_questions,
            questions_with_responses=questions_with_responses,
        )
        job_description_list.append(jd_item)

    return job_description_list
