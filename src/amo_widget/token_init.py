from amocrm.v2 import tokens
from amocrm.v2.tokens import MemoryTokensStorage
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import REDIRECT_URL, CLIENT_SECRET
from .utils import get_tokens_from_db


async def initialize_token(client_id: str, subdomain: str, session: AsyncSession):
    """Инициализация токена"""

    tokens_user = await get_tokens_from_db(subdomain, session)

    access_token, refresh_token = tokens_user[0], tokens_user[1]

    storage = MemoryTokensStorage()
    storage.save_tokens(access_token, refresh_token)

    tokens.default_token_manager(
        client_id=client_id,
        client_secret=CLIENT_SECRET,
        subdomain=subdomain,
        redirect_url=REDIRECT_URL,
        storage=storage,
    )


async def initialize_token_manager(client_id, subdomain, code):
    """Инициализация менеджера токенов. Получение access токена и refresh"""

    storage = tokens.MemoryTokensStorage()
    tokens.default_token_manager(
        client_id=client_id,
        client_secret=CLIENT_SECRET,
        subdomain=subdomain,
        redirect_url=REDIRECT_URL,
        storage=storage
    )

    tokens.default_token_manager.init(code=code, skip_error=False)

    access_token = tokens.default_token_manager.get_access_token()
    refresh_token = tokens.default_token_manager._storage.get_refresh_token()

    if not (access_token and refresh_token):
        raise ValueError("Tokens didn't create")

    return access_token, refresh_token

