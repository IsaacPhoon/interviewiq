from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from app.core.constants import job_description_constants

if TYPE_CHECKING:
    from app.models import Question, User


COMPANY_NAME_MIN_LENGTH = job_description_constants.COMPANY_NAME_MIN_LENGTH
COMPANY_NAME_MAX_LENGTH = job_description_constants.COMPANY_NAME_MAX_LENGTH
TITLE_MIN_LENGTH = job_description_constants.TITLE_MIN_LENGTH
TITLE_MAX_LENGTH = job_description_constants.TITLE_MAX_LENGTH
DESCRIPTION_TEXT_MIN_LENGTH = job_description_constants.DESCRIPTION_TEXT_MIN_LENGTH
DESCRIPTION_TEXT_MAX_LENGTH = job_description_constants.DESCRIPTION_TEXT_MAX_LENGTH


class StatusEnum(str, Enum):
    PENDING = 'pending'
    QUESTIONS_GENERATED = 'questions_generated'
    ERROR = 'error'


class JobDescription(SQLModel, table=True):
    """Database model for a job description."""

    __tablename__: str = 'job_descriptions'

    id: int | None = Field(default=None, primary_key=True)
    company_name: str
    job_title: str
    description_text: str
    status: StatusEnum = StatusEnum.PENDING
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


class JobDescriptionBase(BaseModel):
    """Base schema for job descriptions."""

    company_name: str = Field(
        min_length=COMPANY_NAME_MIN_LENGTH, max_length=COMPANY_NAME_MAX_LENGTH
    )
    job_title: str = Field(min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH)
    description_text: str = Field(
        min_length=DESCRIPTION_TEXT_MIN_LENGTH, max_length=DESCRIPTION_TEXT_MAX_LENGTH
    )


class JobDescriptionCreate(JobDescriptionBase):
    """Schema for creating a job description."""

    pass


class JobDescriptionResponse(JobDescriptionBase):
    """Schema for a job description response."""

    id: int
    status: StatusEnum
    created_at: datetime
