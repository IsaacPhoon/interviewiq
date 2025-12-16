from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import JobDescription


class User(SQLModel, table=True):
    __tablename__: str = 'users'

    id: int | None = Field(default=None, primary_key=True)
    clerk_id: str = Field(unique=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            onupdate=lambda: datetime.now(timezone.utc),
        ),
    )

    job_descriptions: list['JobDescription'] = Relationship(
        back_populates='user', cascade_delete=True
    )
