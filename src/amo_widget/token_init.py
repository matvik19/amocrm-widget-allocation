from amocrm.v2 import tokens

from src.config import REDIRECT_URL, SUBDOMAIN, CLIENT_SECRET, CLIENT_ID


def initialize_token(subdomain: str):
    """Инициализация токенов"""

    tokens.default_token_manager(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        subdomain=SUBDOMAIN,
        redirect_url=REDIRECT_URL,
        storage=tokens.MemoryTokensStorage(),
    )


