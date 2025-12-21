from fastapi import HTTPException, status
from sqlmodel import distinct, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.job_description import JobDescription, StatusEnum
from app.models.question import Question
from app.models.response import Response
from app.services.claude_service import claude_service


class JobDescriptionService:
    """Service for managing job descriptions."""

    async def get_user_job_description(
        self,
        job_description_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> JobDescription:
        """
        Get a job description and verify the user owns it.

        Performs ownership verification to ensure users can only access
        their own job descriptions.

        Raises:
            HTTPException: 404 if job description not found
            HTTPException: 403 if user doesn't own the job description
        """
        stmt = select(JobDescription).where(JobDescription.id == job_description_id)
        result = await session.exec(stmt)
        job_description = result.one_or_none()

        if job_description is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Job description not found',
            )
        if job_description.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Not authorized to access this job description',
            )

        return job_description

    async def create_entry_and_generate_questions(
        self, job_description: JobDescription, session: AsyncSession
    ) -> JobDescription:
        """
        Create a job description entry and generate interview questions.

        Persists the job description to the database, then generates 5 behavioral
        interview questions using Claude AI. Updates the status to QUESTIONS_GENERATED
        on success or ERROR on failure. Exceptions are caught and stored in the
        error_message field rather than propagated.
        """
        session.add(job_description)
        await session.commit()
        await session.refresh(job_description)

        try:
            await self._generate_and_add_questions_to_db(
                job_description=job_description, session=session
            )
            job_description.status = StatusEnum.QUESTIONS_GENERATED

        except Exception as e:
            job_description.status = StatusEnum.ERROR
            job_description.error_message = str(e)

        session.add(job_description)
        await session.commit()
        await session.refresh(job_description)

        return job_description

    async def regenerate_questions(
        self, job_description: JobDescription, session: AsyncSession
    ) -> JobDescription:
        """
        Regenerate interview questions for a job description.

        Deletes all existing questions for the job description and generates
        a fresh set of 5 questions using Claude AI. Updates the status to
        QUESTIONS_GENERATED on success or ERROR on failure. Clears any previous
        error messages on successful regeneration.
        """
        delete_stmt = select(Question).where(
            Question.job_description_id == job_description.id
        )
        result = await session.exec(delete_stmt)
        questions = result.all()
        for question in questions:
            await session.delete(question)
        await session.commit()
        await session.refresh(job_description)

        try:
            await self._generate_and_add_questions_to_db(
                job_description=job_description, session=session
            )
            job_description.status = StatusEnum.QUESTIONS_GENERATED
            job_description.error_message = None

        except Exception as e:
            job_description.status = StatusEnum.ERROR
            job_description.error_message = str(e)

        session.add(job_description)
        await session.commit()
        await session.refresh(job_description)

        return job_description

    async def count_questions_with_responses(
        self, job_description_id: int, session: AsyncSession
    ) -> tuple[int, int]:
        """
        Count questions with at least one response for a job description.

        Returns (questions_with_responses, total_questions) for progress tracking.
        """
        total_stmt = select(func.count(distinct(Question.id))).where(
            Question.job_description_id == job_description_id
        )
        result = await session.exec(total_stmt)
        total_questions_count = result.one()

        with_responses_stmt = (
            select(func.count(distinct(Question.id)))
            .join(Response)
            .where(Question.job_description_id == job_description_id)
        )
        result = await session.exec(with_responses_stmt)
        questions_with_responses_count = result.one()

        return (questions_with_responses_count, total_questions_count)

    async def _generate_and_add_questions_to_db(
        self, job_description: JobDescription, session: AsyncSession
    ) -> None:
        """
        Generate interview questions with Claude and add them to the database.

        Internal method that calls Claude API service to generate questions and
        persists them to the database. Does not commit the session.
        """
        questions_list = await claude_service.generate_question(
            job_description_text=job_description.description_text,
            company_name=job_description.company_name,
            job_title=job_description.job_title,
        )

        for question_text in questions_list:
            question = Question(
                question_text=question_text,
                job_description_id=job_description.id,  # type: ignore[arg-type]
            )
            session.add(question)


job_description_service = JobDescriptionService()
