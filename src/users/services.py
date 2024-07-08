from sqlalchemy.ext.asyncio import AsyncSession

from .models import Users
from .schemas import UserCreate


async def create_user(user: UserCreate, session: AsyncSession):
    """Создание пользователя в бд"""

    new_user = Users(
        client_id=user.client_id,
        subdomain=user.subdomain,
        access_token=user.access_token,
        refresh_token=user.refresh_token,
    )

    session.add(new_user)
    await session.commit()

    return new_user
