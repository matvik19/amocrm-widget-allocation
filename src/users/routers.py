from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.users.schemas import UserCreate
from src.users.services import initialize_token_manager, create_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.post('/add_user')
async def add_user(client_id: str, code: str, subdomain: str, session: AsyncSession = Depends(get_async_session)):
    """Добавление пользователя в БД, сохранение его access_token и refresh_token"""

    try:
        subdomain = subdomain.split('.')[0]
        token_manager = initialize_token_manager(client_id, subdomain)

        token_manager.init(code=code, skip_error=False)
        access_token = token_manager.get_access_token()
        refresh_token = token_manager._storage.get_refresh_token()

        user = UserCreate(
            client_id=client_id,
            subdomain=subdomain,
            access_token=access_token,
            refresh_token=refresh_token
        )

        await create_user(user, session)

        return {
            'status': 200,
            'message': 'The user was successfully registered',
            'user': {
                'integration_id': f'{user.client_id[:5]}...{user.client_id[-5:]}',
                'subdomain': subdomain,
                'access_token': f'{access_token[:5]}...{access_token[-5:]}',
                'refresh_token': f'{refresh_token[:5]}...{refresh_token[-5:]}',
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))