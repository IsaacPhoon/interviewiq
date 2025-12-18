from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import Question


class Response(SQLModel, table=True):
    """Database model for a response to an interview question."""

    __tablename__: str = 'responses'

    id: int | None = Field(default=None, primary_key=True)
    audio_path: str
    transcript: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    evaluation: 'Evaluation' = Field(
        sa_column=Column(JSONB, nullable=False), default_factory=dict
    )

    question_id: int = Field(foreign_key='questions.id', ondelete='CASCADE')
    question: 'Question' = Relationship(back_populates='responses')


class Scores(BaseModel):
    confidence: int = Field(ge=1, le=10, description='Confidence score 1-10')
    clarity_structure: int = Field(
        ge=1, le=10, description='Clarity/Structure score 1-10'
    )
    technical_depth: int = Field(ge=1, le=10, description='Technical depth score 1-10')
    communication_skills: int = Field(
        ge=1, le=10, description='Communication skills score 1-10'
    )
    relevance: int = Field(ge=1, le=10, description='Relevance score 1-10')


class Feedback(BaseModel):
    confidence: str = Field(description='Feedback on confidence')
    clarity_structure: str = Field(description='Feedback on clarity/structure')
    technical_depth: str = Field(description='Feedback on technical depth')
    communication_skills: str = Field(description='Feedback on communication skills')
    relevance: str = Field(description='Feedback on relevance')


class Evaluation(BaseModel):
    scores: Scores
    feedback: Feedback
    overall_comment: str = Field(description='Overall assessment and improvement areas')
