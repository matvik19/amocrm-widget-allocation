from typing import List

from aiohttp import ClientSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.amo_widget.requests_amocrm import *
from src.amo_widget.schemas import AllocationNewLeadByCompanyContacts
from src.amo_widget.services import *
from src.users.models import Users


async def get_headers(subdomain: str, access_token: str):
    """Получение headers для запросов"""

    headers = {
        "Host": subdomain + ".amocrm.ru",
        "Content - Length": "0",
        "Content - Type": "application / json",
        "Authorization": "Bearer " + access_token,
    }

    return headers


async def get_tokens_from_db(subdomain: str, session: AsyncSession):
    """Запрос на получение токенов пользователя из базы данных"""

    query = select(Users.access_token, Users.refresh_token).filter_by(
        subdomain=subdomain
    )
    result = await session.execute(query)
    tokens_from_db = result.first()

    if not tokens_from_db:
        raise ValueError("Tokens not found")

    return tokens_from_db
