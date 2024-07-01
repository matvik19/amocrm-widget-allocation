from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.users.models import Users


async def get_tokens_from_db(subdomain: str, session: AsyncSession):
    """Запрос на получение токенов пользователя из базы данных"""

    query = select(Users.access_token, Users.refresh_token).filter_by(subdomain=subdomain)
    result = await session.execute(query)
    tokens_from_db = result.first()

    if not tokens_from_db:
        raise ValueError("Tokens not found")

    return tokens_from_db

