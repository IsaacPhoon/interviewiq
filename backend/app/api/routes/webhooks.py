from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.config import settings
from app.core.database import SessionDep
from app.models.user import User

router = APIRouter(prefix='/webhooks', tags=['Webhooks'])


async def handle_user_created(session: AsyncSession, user_data: dict):
    """Handle user.created webhook event."""
    clerk_id = user_data['id']
    created_at = datetime.fromtimestamp(user_data['created_at'] / 1000, tz=UTC)
    updated_at = created_at

    user = User(
        clerk_id=clerk_id,
        created_at=created_at,
        updated_at=updated_at,
    )
    session.add(user)
    await session.commit()


async def handle_user_deleted(session: AsyncSession, user_data: dict):
    """Handle user.deleted webhook event."""
    clerk_id = user_data['id']

    result = await session.exec(select(User).where(User.clerk_id == clerk_id))
    user = result.one_or_none()
    if user is not None:
        await session.delete(user)
        await session.commit()


async def handle_user_updated(session: AsyncSession, user_data: dict):
    """Handle user.updated webhook event."""
    pass  # Implement user update logic if needed


EVENT_HANDLERS = {
    'user.created': handle_user_created,
    'user.deleted': handle_user_deleted,
    'user.updated': handle_user_updated,
}


@router.post('/clerk', status_code=status.HTTP_204_NO_CONTENT)
async def clerk_webhook(request: Request, session: SessionDep):
    """
    Handle Clerk authentication webhook events.

    Processes user lifecycle events from Clerk:
    (user.created, user.deleted, user.updated).
    Webhook signature is verified using Svix.

    Returns 400 if verification fails.
    """
    headers = dict(request.headers)
    payload = await request.body()

    try:
        wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
        content = wh.verify(payload, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST) from None

    event_type = content['type']
    handler = EVENT_HANDLERS.get(event_type)

    if handler:
        await handler(session, content['data'])

    return None
