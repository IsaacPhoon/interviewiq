from fastapi import HTTPException, status
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.job_description import JobDescription
from app.models.question import Question
from app.models.response import Response


class QuestionService:
    """Service for managing questions."""

    async def get_user_question(
        self,
        question_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> Question:
        """
        Get a question and verify the user owns it.

        Performs ownership verification to ensure users can only access
        their own questions.

        Raises:
            HTTPException: 404 if question not found or user doesn't own it
        """
        stmt = (
            select(Question).join(JobDescription).where(Question.id == question_id, JobDescription.user_id == user_id)
        )
        result = await session.exec(stmt)
        question = result.one_or_none()

        if question is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Question not found',
            )

        return question

    async def get_job_description_questions(
        self,
        job_description_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> list[Question]:
        """
        Get all questions for a job description with ownership verification.

        Raises:
            HTTPException: 404 if job description not found or user doesn't own it
        """
        jd_stmt = select(JobDescription).where(
            JobDescription.id == job_description_id, JobDescription.user_id == user_id
        )
        jd_result = await session.exec(jd_stmt)
        if jd_result.one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Job description not found',
            )

        questions_stmt = select(Question).where(Question.job_description_id == job_description_id)
        questions_result = await session.exec(questions_stmt)
        return list(questions_result.all())

    async def count_responses(self, question_id: int, session: AsyncSession) -> int:
        """
        Count responses to an interview question.

        Returns the number of responses associated with the given question ID.
        """
        count_stmt = select(func.count(col(Response.id))).where(Response.question_id == question_id)
        result = await session.exec(count_stmt)
        response_count = result.one()

        return response_count


question_service = QuestionService()
