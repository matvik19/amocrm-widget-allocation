import logging
from typing import List, Dict

from fastapi import HTTPException
from sqlalchemy import select, insert, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.managers.models import ManagerStatus


async def create_managers_in_db(managers: dict, subdomain: str, session: AsyncSession):
    """Создать менеджеров со статусами и субдоменом"""

    try:
        for manager_id, is_active in managers.items():
            stmt = insert(ManagerStatus).values(
                manager_id=manager_id, subdomain=subdomain, is_active=is_active
            )
            await session.execute(stmt)

        await session.commit()

    except SQLAlchemyError as e:
        await session.rollback()
        logging.exception("Database error occurred: %s", str(e))
        raise HTTPException(status_code=500, detail="Database error occurred.")


async def get_managers_from_db(subdomain: str, session: AsyncSession):
    """Получить всех менеджеров по subdomain"""

    try:
        query = select(ManagerStatus).filter_by(subdomain=subdomain)
        result = await session.execute(query)

        return result.scalars().all()

    except SQLAlchemyError as e:
        logging.exception("Database error occurred: %s", str(e))
        raise HTTPException(status_code=500, detail="Database error occurred.")


async def update_statuses_managers_in_db(managers: dict, session: AsyncSession):
    """Обновить статусы активности менеджеров по id менеджеров"""

    try:
        for manager_id, is_active in managers.items():
            stmt = (
                update(ManagerStatus)
                .filter_by(manager_id=manager_id)
                .values(is_active=is_active)
            )
            await session.execute(stmt)

        await session.commit()

    except SQLAlchemyError as e:
        await session.rollback()
        logging.exception("Database error occurred: %s", str(e))
        raise HTTPException(status_code=500, detail="Database error occurred.")
