from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import Question, User


class StatusEnum(str, Enum):
    PENDING = 'pending'
    QUESTIONS_GENERATED = 'questions_generated'
    ERROR = 'error'


class JobDescription(SQLModel, table=True):
    __tablename__: str = 'job_descriptions'

    id: int | None = Field(default=None, primary_key=True)
    company_name: str
    job_title: str
    description_text: str
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    error_message: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    user_id: int = Field(foreign_key='users.id', ondelete='CASCADE')
    user: 'User' = Relationship(back_populates='job_descriptions')

    questions: list['Question'] = Relationship(
        back_populates='job_description', cascade_delete=True
    )
