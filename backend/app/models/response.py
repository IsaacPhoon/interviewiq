from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from app.services.claude_service import Evaluation

if TYPE_CHECKING:
    from app.models import Question


class Response(SQLModel, table=True):
    """Database model for a response to an interview question."""

    __tablename__: str = 'responses'

    id: int | None = Field(default=None, primary_key=True)
    audio_path: str
    transcript: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    evaluation: Evaluation = Field(sa_column=Column(JSONB, nullable=False), default_factory=dict)

    question_id: int = Field(foreign_key='questions.id', ondelete='CASCADE')
    question: Question = Relationship(back_populates='responses')
