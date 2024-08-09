import logging
from typing import List

from aioredis import Redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import CLIENT_ID
from src.database import get_async_session, get_redis
from src.managers.models import ManagerStatus
from redis import asyncio as aioredis
from typing import List, Dict

from src.managers.schemas import CreateManagers, UpdateManagers
from src.managers.services import (
    create_managers_in_db,
    get_managers_from_db,
    update_statuses_managers_in_db,
)

router = APIRouter(prefix="/managers", tags=["Managers"])


@router.patch("/update")
async def update_managers(
    data: UpdateManagers, session: AsyncSession = Depends(get_async_session)
):
    await update_statuses_managers_in_db(data.managers, session)

    return {
        "status": "success",
        "data": data.managers,
        "message": "Managers updated successfully",
    }


@router.get("/get")
async def get_managers(
    subdomain: str, session: AsyncSession = Depends(get_async_session)
):
    managers = await get_managers_from_db(subdomain, session)
    if not managers:
        raise HTTPException(status_code=404, detail="Managers not found.")

    return {
        "status": "success",
        "data": managers,
        "message": f"Managers by subdomain={subdomain} with statuses were successfully get",
    }


@router.post("/create")
async def add_managers(
    data: CreateManagers, session: AsyncSession = Depends(get_async_session)
):
    await create_managers_in_db(data.managers, data.subdomain, session)

    return {
        "status": "success",
        "data": data.managers,
        "message": "Managers with statuses were successfully added to the database",
    }
