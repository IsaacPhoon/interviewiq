from fastapi import APIRouter, status
from sqlmodel import col, select

from app.core.auth import CurrentUserDep
from app.core.database import SessionDep
from app.models.job_description import (
    JobDescription,
    JobDescriptionCreate,
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
    updated_job_description = (
        await job_description_service.create_entry_and_generate_questions(
            job_description=db_job_description, session=session
        )
    )
    return updated_job_description


@router.post(
    '/{job_description_id}/regenerate-questions', response_model=JobDescriptionResponse
)
async def regenerate_questions(
    job_description_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    job_description = await job_description_service.get_user_job_description(
        job_description_id=job_description_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    updated_job_description = await job_description_service.regenerate_questions(
        job_description=job_description, session=session
    )

    return updated_job_description


@router.get('/', response_model=list[JobDescriptionResponse])
async def get_job_descriptions(
    current_user: CurrentUserDep, session: SessionDep, limit: int = 10, offset: int = 0
):
    stmt = (
        select(JobDescription)
        .where(JobDescription.user_id == current_user.id)
        .order_by(col(JobDescription.created_at).desc())
        .offset(offset)
        .limit(limit)
    )
    job_descriptions = await session.exec(stmt)

    job_description_list = []
    for jd in job_descriptions:
        jd_item = await JobDescriptionResponse.from_job_description(
            job_description=jd, session=session
        )
        job_description_list.append(jd_item)

    return job_description_list


@router.get('/{job_description_id}', response_model=JobDescriptionResponse)
async def get_job_description(
    job_description_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    jd = await job_description_service.get_user_job_description(
        job_description_id=job_description_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    return await JobDescriptionResponse.from_job_description(
        job_description=jd, session=session
    )


@router.delete('/{job_description_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_description(
    job_description_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    jd = await job_description_service.get_user_job_description(
        job_description_id=job_description_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    await session.delete(jd)
    await session.commit()
