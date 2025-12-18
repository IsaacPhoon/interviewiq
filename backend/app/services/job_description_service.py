from sqlmodel import distinct, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.job_description import JobDescription, StatusEnum
from app.models.question import Question
from app.models.response import Response
from app.services.claude_service import claude_service


class JobDescriptionService:
    """Service for managing job descriptions."""

    async def create_entry_and_generate_questions(
        self, job_description: JobDescription, session: AsyncSession
    ) -> JobDescription:
        """Create a job description entry and generate interview questions."""
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

    async def count_questions_with_responses(
        self, job_description_id: int, session: AsyncSession
    ) -> tuple[int, int]:
        """
        Count questions with at least one response for a job description.
        Return a tuple of (questions_with_responses, total_questions).
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
        """Generate interview questions with Claude and add them to the database."""
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
