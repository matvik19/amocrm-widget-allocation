import datetime

from amocrm.v2.entity.note import _Note
from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from .schemas import *
from src.amo_widget.token_init import initialize_token
from .services import *
from ..database import get_async_session

router = APIRouter(prefix="/widget", tags=["Widget"])


@router.patch("/config_widget")
async def config_widget(data: ConfigWidgetBody, session: AsyncSession = Depends(get_async_session)):
    """Настройка виджета (триггера)"""

    params = data.dict()

    await initialize_token(data.client_id, data.subdomain, session)

    tokens = await get_tokens_from_db(data.subdomain, session)
    access_token = tokens[0]

    headers = await get_headers(data.subdomain, access_token)

    await allocation_new_lead(params, data.subdomain, headers, session)

    # Дополнительное распределение
    if data.use_company:
        await allocation_all_leads_by_companies(AllocationAllByCompanyContacts(**params), headers)

    if data.use_contact:
        await allocation_all_leads_by_contacts(AllocationAllByCompanyContacts(**params), headers)


@router.get("/get")
async def get(client_id: str, subdomain: str, session: AsyncSession = Depends(get_async_session)):
    try:
        tokens = await get_tokens_from_db(subdomain, session)
        access_token = tokens[0]
        headers = await get_headers(subdomain, access_token)
        await initialize_token(client_id, subdomain, session)

        return {
            "status": "success",
            "message": None,
            "data": None
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))