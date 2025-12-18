from anthropic import AsyncAnthropic, DefaultAioHttpClient
from pydantic import BaseModel, Field

from app.core.config import settings

QUESTION_GENERATION_PROMPT = """
You are an expert interview coach. Based on the following job description, generate exactly 5 behavioral interview questions that are tailored to this specific role.

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


class QuestionsList(BaseModel):
    """Schema for generated interview questions."""

    questions: list[str] = Field(
        min_length=5,
        max_length=5,
        description='List of exactly 5 behavioral interview questions',
    )


class ClaudeServiceError(Exception):
    """Raised when there is an error interacting with the Claude API."""

    pass


class ClaudeService:
    """Service to interact with the Claude API."""

    def __init__(self):
        self.client = AsyncAnthropic(
            api_key=settings.CLAUDE_API_KEY,
            http_client=DefaultAioHttpClient(),
        )
        self.model = settings.CLAUDE_MODEL

    async def generate_question(
        self, job_description_text: str, company_name: str, job_title: str
    ) -> list[str]:
        """Generate 5 interview questions based on the job description using Claude API."""
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
            questions_list = response.parsed_output
            if questions_list is None:
                raise ClaudeServiceError(
                    'Error generating questions with Claude API: Empty/invalid output received.'
                )
        except Exception as e:
            raise ClaudeServiceError(
                f'Error generating questions with Claude API: {str(e)}'
            )

        return questions_list.questions


claude_service = ClaudeService()
