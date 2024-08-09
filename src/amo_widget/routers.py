import datetime

from amocrm.v2 import Pipeline
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from .schemas import *
from src.amo_widget.token_init import initialize_token
from .services import *
from .utils import get_tokens_from_db, get_headers
from ..database import get_async_session

router = APIRouter(prefix="/widget", tags=["Widget"])


@router.patch("/config_widget", response_model=ConfigResponse)
async def config_widget(
    data: ConfigWidgetBody,
    session: AsyncSession = Depends(get_async_session),
    client_session: ClientSession = Depends(get_client_session),
):
    """Настройка виджета (триггера)"""
    try:
        await initialize_token(data.client_id, data.subdomain, session)

        params = data.dict()

        tokens = await get_tokens_from_db(data.subdomain, session)
        access_token = tokens[0]

        headers = await get_headers(data.subdomain, access_token)

        if data.ignore_manager:
            print("Зашли в распределение")
            await allocation_new_lead_by_contact_company(
                params, headers, client_session
            )
            return ConfigResponse(
                status="success",
                lead_id=data.lead_id,
                massage="The distribution was successful, taking into account contacts and companies",
            )
        else:
            await allocation_new_lead(params, headers, client_session)
            return ConfigResponse(
                status="success",
                lead_id=data.lead_id,
                message="The distribution was successful without taking into account contacts and companies",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get")
async def get(
    client_id: str,
    subdomain: str,
    session: AsyncSession = Depends(get_async_session),
    client_session: ClientSession = Depends(get_client_session),
):
    try:
        tokens = await get_tokens_from_db(subdomain, session)
        access_token = tokens[0]
        headers = await get_headers(subdomain, access_token)
        await initialize_token(client_id, subdomain, session)

        # lead = await get_lead_by_id(17539645, subdomain, headers, client_session)
        # contacts = lead["_embedded"]["contacts"]

        p = Pipeline.objects.get(object_id=7991514)
        for s in p.statuses:
            print(s.id, s.name)

        # print("СДЕЛКА", lead)
        # print("АЙДИ КОНТАКТА СДЕЛКИ:", lead["_embedded"]["contacts"])

        # leads_andrey = await get_leads_by_filter_async(
        #     subdomain,
        #     headers,
        #     responsible_user_id=11317986,
        #     pipeline_id=8430722,
        #     status_id=68604810,
        # )
        # leads_dmitry = await get_leads_by_filter_async(
        #     subdomain,
        #     headers,
        #     responsible_user_id=9606738,
        #     pipeline_id=8319714,
        #     status_id=67829730,
        # )
        # leads_in_pipeline = await get_leads_by_filter_async(
        #     subdomain, headers, pipeline_id=8319714, status_id=67829730
        # )
        #
        # print("ВСЕГО СДЕЛОК:", len(leads_in_pipeline))
        # print("СДЕЛОК У АНДРЕЯ:", len(leads_andrey))
        # print("СДЕЛОК У ДМИТРИЯ:", len(leads_dmitry))
        #
        # return {
        #     "status": "success",
        #     "message": None,
        #     "data": {
        #         "leads_andrey": leads_andrey,
        #         "leads_dmitry": leads_dmitry,
        #         "leads_in_pipeline": leads_in_pipeline,
        #     },
        # }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
