from fastapi import APIRouter

from app.api.routes import job_descriptions, webhooks

api_router = APIRouter()
api_router.include_router(webhooks.router)
api_router.include_router(job_descriptions.router)


@api_router.get('/health', tags=['Health'])
def check_health():
    return {'status': 'healthy'}
