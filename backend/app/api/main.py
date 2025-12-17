from fastapi import APIRouter

from app.api.routes import webhooks

api_router = APIRouter()
api_router.include_router(webhooks.router)


@api_router.get('/health')
def check_health():
    return {'status': 'healthy'}
