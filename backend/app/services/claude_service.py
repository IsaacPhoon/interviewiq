from anthropic import (
    APIConnectionError,
    APIStatusError,
    AsyncAnthropic,
    DefaultAioHttpClient,
)
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings

QUESTION_GENERATION_PROMPT = """
You are an expert interview coach. Based on the following job description, \
generate exactly 5 behavioral interview questions that are tailored to this \
specific role.

Company: {company_name}
Job Title: {job_title}

Job Description:
{job_description_text}

Generate 5 behavioral interview questions that:
1. Are specific to this role and company
2. Follow the STAR method (Situation, Task, Action, Result)
3. Test relevant competencies for this position
4. Are clear and professionally worded
5. Cover different aspects of the role
"""


class ClaudeServiceError(Exception):
    """Raised when there is an error interacting with the Claude API."""

    pass


class QuestionsList(BaseModel):
    """Schema for generated interview questions."""

    questions: list[str] = Field(
        min_length=5,
        max_length=5,
        description='List of exactly 5 behavioral interview questions',
    )


class ClaudeService:
    """
    Service to interact with the Claude API.

    Handles all Claude API communication for generating behavioral interview
    questions using structured outputs. Configured with API key and model
    from application settings.
    """

    def __init__(self):
        """Initialize the ClaudeService with async API client and model settings."""
        self.client = AsyncAnthropic(
            api_key=settings.CLAUDE_API_KEY,
            http_client=DefaultAioHttpClient(),
        )
        self.model = settings.CLAUDE_MODEL

    async def generate_question(
        self, job_description_text: str, company_name: str, job_title: str
    ) -> list[str]:
        """
        Generate 5 behavioral interview questions using Claude API.

        Uses Claude's structured output feature to generate STAR method-based
        questions tailored to the specific role and company.
        Returns a list of exactly 5 questions.

        Raises:
            ClaudeServiceError: If API call fails or returns invalid output
        """
        try:
            response = await self.client.beta.messages.parse(
                model=self.model,
                max_tokens=2000,
                betas=['structured-outputs-2025-11-13'],
                messages=[
                    {
                        'role': 'user',
                        'content': QUESTION_GENERATION_PROMPT.format(
                            company_name=company_name,
                            job_title=job_title,
                            job_description_text=job_description_text,
                        ),
                    }
                ],
                output_format=QuestionsList,
            )
        except APIConnectionError as e:
            raise ClaudeServiceError(
                f'Failed to connect to Claude API: {str(e)}'
            ) from e
        except APIStatusError as e:
            raise ClaudeServiceError(
                f'Claude API request failed: {str(e)}. Status code: {e.status_code}'
            ) from e
        except ValidationError as e:
            raise ClaudeServiceError(
                f'Failed to validate Claude API response: {str(e)}'
            ) from e
        except Exception as e:
            raise ClaudeServiceError(
                f'Unexpected error during question generation. '
                f'{type(e).__name__}: {str(e)}'
            ) from e

        questions_list = response.parsed_output

        if questions_list is None:
            raise ClaudeServiceError(
                'Claude API returned empty response. '
                'The model may have failed to generate structured output.'
            )

        return questions_list.questions


claude_service = ClaudeService()
