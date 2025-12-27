from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from app.models.enums import ResponseProcessingStatus
from app.services.claude_service import Evaluation, Feedback, Scores

if TYPE_CHECKING:
    from app.models import Question


class Response(SQLModel, table=True):
    """Database model for a response to an interview question."""

    __tablename__: str = 'responses'

    id: int | None = Field(default=None, primary_key=True)
    audio_path: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    status: ResponseProcessingStatus = ResponseProcessingStatus.PENDING
    error_message: str | None = None
    processing_started_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    processing_completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    transcript: str | None = None
    evaluation: dict | None = Field(sa_column=Column(JSONB), default=None)

    question_id: int = Field(foreign_key='questions.id', ondelete='CASCADE', index=True)
    question: Question = Relationship(back_populates='responses')

    @property
    def evaluation_obj(self) -> Evaluation | None:
        """Get the evaluation attribute as an Evaluation Pydantic object."""
        if self.evaluation is not None:
            return Evaluation.model_validate(self.evaluation)
        return None

    @evaluation_obj.setter
    def evaluation_obj(self, value: Evaluation | None) -> None:
        """Set the evaluation attribute from an Evaluation Pydantic object."""
        if value is not None:
            self.evaluation = value.model_dump()
        else:
            self.evaluation = None


class ResponseInitialResponse(BaseModel):
    """
    Response schema for the initial submission of a response.

    Includes the response ID, processing status, creation timestamp, and a confirmation message.
    """

    id: int
    status: ResponseProcessingStatus
    created_at: datetime
    message: str = 'Response submitted successfully and is being processed in the background.'


class ResponsePollingResponse(BaseModel):
    """
    Response schema for polling the status of a response processing.

    ALways includes the response ID, processing status, creation timestamp, and a message.
    Includes progressive disclosure of additional fields as processing advances and/or completes.
    """

    id: int
    status: ResponseProcessingStatus
    created_at: datetime
    message: str

    transcript: str | None = None

    scores: Scores | None = None
    feedback: Feedback | None = None
    overall_comment: str | None = None

    @property
    def evaluation(self) -> Evaluation | None:
        """Get the evaluation fields as an Evaluation Pydantic object."""
        if self.scores is not None and self.feedback is not None and self.overall_comment is not None:
            return Evaluation(
                scores=self.scores,
                feedback=self.feedback,
                overall_comment=self.overall_comment,
            )
        return None

    @evaluation.setter
    def evaluation(self, value: Evaluation | None) -> None:
        """Set the evaluation fields from an Evaluation Pydantic object."""
        if value is not None:
            self.scores = value.scores
            self.feedback = value.feedback
            self.overall_comment = value.overall_comment
        else:
            self.scores = None
            self.feedback = None
            self.overall_comment = None
