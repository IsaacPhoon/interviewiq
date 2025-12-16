from fastapi import APIRouter

api_router = APIRouter()


@api_router.get('/health')
def check_health():
    return {'status': 'healthy'}
