from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.users.schemas import UserCreate
from src.users.services import create_user
from src.amo_widget.token_init import initialize_token_manager

router = APIRouter(prefix="/users", tags=["Users"])


@router.post('/add_user')
async def add_user(client_id: str, code: str, subdomain: str, session: AsyncSession = Depends(get_async_session)):
    """Добавление пользователя в БД, сохранение его access_token и refresh_token"""

    try:
        subdomain = subdomain.split('.')[0]

        access_token, refresh_token = await initialize_token_manager(client_id, subdomain, code)

        user = UserCreate(
            client_id=client_id,
            subdomain=subdomain,
            access_token=access_token,
            refresh_token=refresh_token
        )

        await create_user(user, session)

        return {
            "status": "success",
            "message": "The user was successfully registered",
            "data": {
                'integration_id': f'{user.client_id[:5]}...{user.client_id[-5:]}',
                'subdomain': subdomain,
                'access_token': f'{access_token[:5]}...{access_token[-5:]}',
                'refresh_token': f'{refresh_token[:5]}...{refresh_token[-5:]}',
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=500, detail={
            "status": "Error",
            "message": str(e),
            "data": None
        })

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=500, detail={
            "status": "Error",
            "message": str(SQLAlchemyError),
            "data": None
        })

