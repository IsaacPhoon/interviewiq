from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from app.models import JobDescription, Response


class Question(SQLModel, table=True):
    """
    Database model for an interview question.

    Represents a behavioral interview question associated with a job description.
    Includes relationships to the job description and user responses.
    """

    __tablename__: str = 'questions'

    id: int | None = Field(default=None, primary_key=True)
    question_text: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    job_description_id: int = Field(foreign_key='job_descriptions.id', ondelete='CASCADE', index=True)
    job_description: JobDescription = Relationship(back_populates='questions')

    responses: list[Response] = Relationship(back_populates='question', cascade_delete=True)


class QuestionResponse(BaseModel):
    """
    Response schema for an interview question.

    Includes the question details along with the calculated count of user attempts.
    """

    id: int
    question_text: str
    created_at: datetime
    attempt_count: int

    @classmethod
    async def from_question(cls, question: Question, session: AsyncSession) -> QuestionResponse:
        from app.services.question_service import question_service

        attempt_count = await question_service.count_responses(
            question_id=question.id,  # type: ignore[arg-type]
            session=session,
        )

        return cls(
            **question.model_dump(exclude={'job_description', 'responses'}),
            attempt_count=attempt_count,
        )
