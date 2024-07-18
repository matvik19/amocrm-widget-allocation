import aiohttp
from amocrm.v2 import tokens
from amocrm.v2.tokens import MemoryTokensStorage
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URL
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
    """Инициализация менеджера токенов. Первое получение access токена и refresh"""

    storage = tokens.MemoryTokensStorage()
    tokens.default_token_manager(
        client_id=client_id,
        client_secret=CLIENT_SECRET,
        subdomain=subdomain,
        redirect_url=REDIRECT_URL,
        storage=storage,
    )

    tokens.default_token_manager.init(code=code, skip_error=False)

    access_token = tokens.default_token_manager.get_access_token()
    refresh_token = tokens.default_token_manager._storage.get_refresh_token()

    if not (access_token and refresh_token):
        raise ValueError("Tokens didn't create")

    return access_token, refresh_token


async def get_new_tokens(subdomain: str, refresh_token: str):
    """Повторное получение новых токенов с помощью refresh_token"""

    url = f"https://{subdomain}.amocrm.ru/oauth2/access_token"
    headers = {
        "Content-Type": "application/json",
    }
    body = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    try:
        async with aiohttp.ClientSession() as client_session:
            async with client_session.post(url, json=body, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    new_access_token = data.get("access_token")
                    new_refresh_token = data.get("refresh_token")

                    if not new_access_token and not new_refresh_token:
                        raise ValueError("Missing tokens in response")

                    return new_access_token, new_refresh_token
                else:
                    error_message = await response.text()
                    raise ValueError(f"Failed to fetch tokens: {error_message}")

    except aiohttp.ClientError as e:
        raise ValueError(f"HTTP client error: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {e}")
