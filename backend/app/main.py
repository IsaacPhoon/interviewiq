from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.main import api_router
from app.services.openai_service import openai_service
from app.services.r2_storage_service import r2_storage_service
from app.services.transcription_service import transcription_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    openai_service.start()
    r2_storage_service.start()
    transcription_service.start()

    yield

    # Shutdown
    await openai_service.stop()
    r2_storage_service.stop()
    await transcription_service.stop()


app = FastAPI(lifespan=lifespan)


app.include_router(api_router, prefix='/api/v1')
