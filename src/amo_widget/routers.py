import datetime

from fastapi import APIRouter, Depends, HTTPException

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

    if data.accept_to_existing_leads:

        # Основное распределение
        if data.mode == 'percent':
            await allocation_all_leads_by_percent(AllocationAllByPercentBody(**params), headers)

        elif data.mode == 'max_count':
            await allocation_all_leads_by_max_count(AllocationAllByMaxCountBody(**params), headers)

        else:
            return f'Неверно передан режим. Получено: {data.mode}'

        # Дополнительное распределение
        if data.use_company:
            await allocation_all_leads_by_companies(AllocationAllByCompanyContacts(**params), headers)

        if data.use_contact:
            await allocation_all_leads_by_contacts(AllocationAllByCompanyContacts(**params), headers)

    return f'/trigger_allocation?users={data.users_ids}&percents={data.percents}%use_contact={data.use_contact}'


@router.patch("/trigger_allocation")
async def trigger():
    pass


@router.patch("/integration")
async def trigger():
    pass


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
            "data": await get_leads_by_filter_async(subdomain, headers, pipeline_id=8319714, status_id=67829730)
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
