from fastapi import Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.amo_widget.token_init import get_new_tokens
from src.config import CLIENT_ID
from src.database import get_async_session, async_session_maker
from src.users.models import Users


async def update_tokens():
    """Обновление access_token, refresh_token по старому refresh_tonken пользователя"""

    try:
        async with async_session_maker() as session:
            result = await session.execute(select(Users).filter_by(client_id=CLIENT_ID))
            users = result.scalars().all()
            print("Получаем пользователей из бд", users)

            for user in users:
                new_access_token, new_refresh_token = await get_new_tokens(
                    user.subdomain, user.refresh_token
                )

                if new_access_token and new_refresh_token:
                    stmt = update(Users).values(
                        access_token=new_access_token,
                        refresh_token=new_refresh_token,
                    )
                    await session.execute(stmt)
                    await session.commit()

    except Exception as e:
        ValueError(f"Ошибка записи новых токенов: {e}")


def activate_background_task():
    """Запуск фоновой задачи update_tokens"""

    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_tokens, IntervalTrigger(minutes=1))
    scheduler.start()
