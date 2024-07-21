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
async def config_widget(
    data: ConfigWidgetBody,
    session: AsyncSession = Depends(get_async_session),
    client_session: ClientSession = Depends(get_client_session),
):
    """Настройка виджета (триггера)"""

    await initialize_token(data.client_id, data.subdomain, session)

    params = data.dict()

    tokens = await get_tokens_from_db(data.subdomain, session)
    access_token = tokens[0]

    headers = await get_headers(data.subdomain, access_token)

    await allocation_new_lead(params, data.subdomain, headers, client_session)
    print("Вышли из распределение процентов")

    if data.use_contact:
        print("Зашли в распределение по контакту")
        await allocation_new_lead_by_contacts(
            AllocationNewLeadByCompanyContacts(**params), headers, client_session
        )

    if data.use_company:
        await allocation_new_lead_by_company(
            AllocationNewLeadByCompanyContacts(**params), headers, client_session
        )


# @router.get("/get")
# async def get(
#     client_id: str, subdomain: str, session: AsyncSession = Depends(get_async_session)
# ):
#     try:
#         tokens = await get_tokens_from_db(subdomain, session)
#         access_token = tokens[0]
#         headers = await get_headers(subdomain, access_token)
#         await initialize_token(client_id, subdomain, session)
#
#         leads_andrey = await get_leads_by_filter_async(
#             subdomain,
#             headers,
#             responsible_user_id=5837446,
#             pipeline_id=8319714,
#             status_id=67829730,
#         )
#         leads_dmitry = await get_leads_by_filter_async(
#             subdomain,
#             headers,
#             responsible_user_id=9606738,
#             pipeline_id=8319714,
#             status_id=67829730,
#         )
#         leads_in_pipeline = await get_leads_by_filter_async(
#             subdomain, headers, pipeline_id=8319714, status_id=67829730
#         )
#
#         print("ВСЕГО СДЕЛОК:", len(leads_in_pipeline))
#         print("СДЕЛОК У АНДРЕЯ:", len(leads_andrey))
#         print("СДЕЛОК У ДМИТРИЯ:", len(leads_dmitry))
#
#         return {
#             "status": "success",
#             "message": None,
#             "data": {
#                 "leads_andrey": leads_andrey,
#                 "leads_dmitry": leads_dmitry,
#                 "leads_in_pipeline": leads_in_pipeline,
#             },
#         }
#
#     except ValueError as e:
#         raise HTTPException(status_code=404, detail=str(e))
