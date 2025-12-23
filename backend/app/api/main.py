from fastapi import APIRouter

from app.api.routes import job_descriptions, questions, webhooks

api_router = APIRouter()
api_router.include_router(job_descriptions.router)
api_router.include_router(questions.router)
api_router.include_router(webhooks.router)


@api_router.get('/health', tags=['Health'])
async def check_health():
    """
    Health check endpoint.

    Returns the application health status. Used for monitoring
    and load balancer health checks.
    """
    return {'status': 'healthy'}
