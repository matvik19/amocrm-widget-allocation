from amocrm.v2 import tokens
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from .models import Users
from .schemas import UserCreate
from src.config import CLIENT_SECRET, REDIRECT_URL


def initialize_token_manager(client_id: str, subdomain: str):
    """ Инициализация менеджер токенов """

    return tokens.default_token_manager(
        client_id=client_id,
        client_secret=CLIENT_SECRET,
        subdomain=subdomain,
        redirect_url=REDIRECT_URL,
        storage=tokens.MemoryTokensStorage()
    )


async def create_user(user: UserCreate, session: AsyncSession):
    """Создание пользователя в бд"""

    try:
        new_user = Users(
            client_id=user.client_id,
            subdomain=user.subdomain,
            access_token=user.access_token,
            refresh_token=user.refresh_token,
        )

        session.add(new_user)
        await session.commit()

        return new_user

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(SQLAlchemyError))
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail={"status": "error"})
