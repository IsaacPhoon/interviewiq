from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.config import settings
from app.core.database import SessionDep
from app.models.user import User

router = APIRouter(prefix='/webhooks', tags=['Webhooks'])


@router.post('/clerk', status_code=status.HTTP_204_NO_CONTENT)
async def clerk_webhook(request: Request, session: SessionDep):
    headers = dict(request.headers)
    payload = await request.body()

    try:
        wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
        content = wh.verify(payload, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    event_type = content['type']

    if event_type == 'user.created':
        user_data = content['data']
        clerk_id = user_data['id']
        created_at = datetime.fromtimestamp(
            user_data['created_at'] / 1000, tz=timezone.utc
        )
        updated_at = created_at

        user = User(
            clerk_id=clerk_id,
            created_at=created_at,
            updated_at=updated_at,
        )
        session.add(user)
        await session.commit()

    elif event_type == 'user.deleted':
        user_data = content['data']
        clerk_id = user_data['id']

        result = await session.exec(select(User).where(User.clerk_id == clerk_id))
        user = result.one_or_none()
        if user is not None:
            await session.delete(user)
            await session.commit()

    elif event_type == 'user.updated':
        pass

    return None
