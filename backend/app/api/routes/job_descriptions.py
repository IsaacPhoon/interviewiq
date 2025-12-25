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

router = APIRouter(prefix='/job-descriptions', tags=['Job Descriptions'])


@router.post(
    path='/',
    status_code=status.HTTP_201_CREATED,
    response_model=JobDescriptionResponse,
)
async def create_job_description(
    job_description: JobDescriptionCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Create a new job description and generate interview questions.

    Creates a job description entry and asynchronously generates 5 behavioral
    interview questions tailored to the role using Claude API. Returns the created
    job description with status and question count.
    """
    db_job_description = JobDescription.model_validate(job_description, update={'user_id': current_user.id})
    updated_job_description = await job_description_service.create_entry_and_generate_questions(
        job_description=db_job_description, session=session
    )

    return await JobDescriptionResponse.from_job_description(job_description=updated_job_description, session=session)


@router.post(
    path='/{job_description_id}/regenerate-questions',
    response_model=JobDescriptionResponse,
)
async def regenerate_questions(
    job_description_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Regenerate interview questions for an existing job description.

    Deletes existing questions and generates a new set of 5 behavioral
    interview questions using Claude API. Useful when an error occurs
    during initial generation.

    Returns 404 if not found or not owned by user.
    """
    job_description = await job_description_service.get_user_job_description(
        job_description_id=job_description_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    updated_job_description = await job_description_service.regenerate_questions(
        job_description=job_description, session=session
    )

    return await JobDescriptionResponse.from_job_description(job_description=updated_job_description, session=session)


@router.get(
    path='/',
    response_model=list[JobDescriptionResponse],
)
async def get_job_descriptions(
    current_user: CurrentUserDep,
    session: SessionDep,
    limit: int = 10,
    offset: int = 0,
):
    """
    List all job descriptions for the authenticated user.

    Returns a paginated list ordered by creation date (newest first).
    Each entry includes total questions count and answered questions count.
    """
    stmt = (
        select(JobDescription)
        .where(JobDescription.user_id == current_user.id)
        .order_by(col(JobDescription.created_at).desc())
        .offset(offset)
        .limit(limit)
    )
    job_descriptions = await session.exec(stmt)

    job_description_list = []
    for job_description in job_descriptions:
        job_description_item = await JobDescriptionResponse.from_job_description(
            job_description=job_description, session=session
        )
        job_description_list.append(job_description_item)

    return job_description_list


@router.get(
    path='/{job_description_id}',
    response_model=JobDescriptionResponse,
)
async def get_job_description(
    job_description_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Get a specific job description by ID.

    Returns the full job description details including total questions count
    and answered questions count.

    Returns 404 if not found or not owned by user.
    """
    job_description = await job_description_service.get_user_job_description(
        job_description_id=job_description_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    return await JobDescriptionResponse.from_job_description(job_description=job_description, session=session)


@router.delete(
    path='/{job_description_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_job_description(
    job_description_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """
    Delete a job description and all associated data.

    Permanently deletes the job description along with all associated
    questions and responses.

    Returns 404 if not found or not owned by user.
    """
    job_description = await job_description_service.get_user_job_description(
        job_description_id=job_description_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        session=session,
    )

    await session.delete(job_description)
    await session.commit()

    return None
