from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import JobDescription, Response


class Question(SQLModel, table=True):
    __tablename__: str = 'questions'

    id: int | None = Field(default=None, primary_key=True)
    question_text: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    job_description_id: int = Field(
        foreign_key='job_descriptions.id', ondelete='CASCADE'
    )
    job_description: 'JobDescription' = Relationship(back_populates='questions')

    responses: list['Response'] = Relationship(
        back_populates='question', cascade_delete=True
    )
