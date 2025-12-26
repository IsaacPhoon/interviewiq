from enum import Enum


class JobDescriptionStatus(str, Enum):
    """Enumeration of possible statuses during the generation of interview questions for a job description."""

    PENDING = 'pending'
    QUESTIONS_GENERATED = 'questions_generated'
    ERROR = 'error'


class ResponseProcessingStatus(str, Enum):
    """Enumeration of possible statuses during the processing of user responses."""

    PENDING = 'pending'
    TRANSCRIBING = 'transcribing'
    TRANSCRIBED = 'transcribed'
    EVALUATING = 'evaluating'
    EVALUATED = 'evaluated'
    ERROR = 'error'
