import datetime

from fastapi import APIRouter, Depends, HTTPException

from .schemas import *
from src.amo_widget.token_init import initialize_token
from .services import *
from ..database import get_async_session

router = APIRouter(prefix="/widget", tags=["Widget"])


@router.patch("/allocation_by_percents")
async def allocation_new_lead_by_percents(data: AllocationNewLeadByPercentBody, subdomain: str,
                                          session: AsyncSession = Depends(get_async_session)):
    """Распределение новой сделки по процентам"""

    initialize_token()

    data = dict(data)

    pipeline_id = data.get('pipeline_id')
    lead_id = data.get('lead_id')
    users_ids = data.get('users_ids')
    percents = data.get('percents')
    status = data.get('status')
    update_tasks = data.get('update_tasks')

    all_leads = list((await get_leads_by_filter_async(pipeline_id=pipeline_id, status=status)).keys())
    all_leads_count = len(all_leads)

    for i, user_id in enumerate(users_ids):
        target_leads_count = int(all_leads_count * percents[i] / 100)
        user_leads_count = len(await get_leads_by_filter_async(
            pipeline_id=pipeline_id,
            status=status,
            responsible_user_id=user_id,
        ))
        if user_leads_count < target_leads_count:
            await set_responsible_user_in_lead([lead_id], user_id)

        if update_tasks:
            await set_responsible_user_in_task_by_lead([lead_id], user_id)

        break

    return {
        'status': 200,
        'lead': lead_id,
    }


@router.patch("/allocation_new_lead_by_maximum")
async def allocation_new_lead_by_maximum(data: AllocationNewLeadByMaxCountBody):
    """Распределение новой сделки по максимальному количеству"""

    initialize_token()

    data = dict(data)

    update_tasks = data.get('update_tasks')
    lead_id = data.get('lead_id')
    pipeline_id = data.get('pipeline_id')
    users_ids = data.get('users_ids')
    status = data.get('status')
    necessary_quantity_leads = data.get('necessary_quantity_leads')

    users_and_necessary_quantity_leads = dict(zip(users_ids, necessary_quantity_leads))
    users_leads = {user_id: len(await get_leads_by_filter_async(pipeline_id=pipeline_id, status=status,
                                                                responsible_user_id=user_id)) for user_id in users_ids}

    while users_leads:
        user_with_min_quantity_leads = min(users_leads, key=users_leads.get)
        if users_leads[user_with_min_quantity_leads] < users_and_necessary_quantity_leads[user_with_min_quantity_leads]:
            await set_responsible_user_in_lead([lead_id], user_with_min_quantity_leads)

            if update_tasks:
                await set_responsible_user_in_task_by_lead([lead_id], user_with_min_quantity_leads)

            break
        else:
            del users_leads[user_with_min_quantity_leads]

    return {
        'status': 200,
        'lead': lead_id
    }


@router.patch("/allocation_by_contacts")
async def allocation_new_lead_by_contacts(lead_id: int, update_tasks: bool):
    """Распределение новой сделки по контакту"""

    initialize_token()

    contact_id = (await get_contacts_by_lead(lead_id))

    if contact_id:
        responsible_user = await get_responsible_user_contact(contact_id)
    else:
        return {
            'status': 400,
            'lead': lead_id,
        }

    await set_responsible_user_in_lead([lead_id], responsible_user)

    if update_tasks:
        await set_responsible_user_in_task_by_lead([lead_id], responsible_user)

    return {
        'status': 200,
        'lead': lead_id,
    }


@router.patch("/allocation_by_company")
async def allocation_new_lead_by_company(lead_id: int, update_tasks: bool):
    """Распределение новой сделки по компании"""

    initialize_token()

    company_id = await get_company_by_lead(lead_id)

    if company_id:
        responsible_user = await get_responsible_user_company(company_id)
    else:
        return {
            'status': 400,
            'lead': lead_id
        }

    await set_responsible_user_in_lead([lead_id], responsible_user)

    if update_tasks:
        await set_responsible_user_in_task_by_lead([lead_id], responsible_user)

    return {
        'status': 200,
        'lead': lead_id
    }


@router.patch("/allocation_pipeline")
async def allocation_all_leads_by_percent(
        data: AllocationAllByPercentBody, client_id: str,
        subdomain: str, session: AsyncSession = Depends(get_async_session)
):
    """Распределение по процентам всех сделок в этапе"""

    await initialize_token(client_id, subdomain, session)
    start = datetime.datetime.now()
    data = dict(data)

    pipeline_id = data.get('pipeline_id')
    users_ids = data.get('users_ids')
    percents = data.get('percents')
    status = data.get('status')
    update_tasks = data.get('update_tasks')

    # Получаем список всех сделок
    leads = list((await get_leads_by_filter_async(subdomain, session, pipeline_id=pipeline_id, status=status)).keys())

    for i, user_id in enumerate(users_ids):
        target_leads_count = int(len(leads) * percents[i] / 100)

        if (i + 1) == len(users_ids):
            user_leads = leads
        else:
            user_leads = leads[:target_leads_count]
            leads = leads[target_leads_count:]

        await set_responsible_user_in_lead(user_leads, user_id, subdomain, session)

        if update_tasks:
            await set_responsible_user_in_task_by_lead(user_leads, user_id, subdomain, session)

    end = datetime.datetime.now()

    return {'status': 200,
            "time_process": (end - start),
            'data': {
                'users': users_ids,
                'percents': percents,
                'leads': leads
            }}


@router.patch("/allocation_all_leads_by_max_count")
async def allocation_all_leads_by_max_count(data: AllocationAllByMaxCountBody):
    """Распределение всех сделок по максимальному количеству"""

    initialize_token()
    start = datetime.datetime.now()
    data = dict(data)

    pipeline_id = data.get('pipeline_id')
    users_ids = data.get('users_ids')
    necessary_quantity_leads = data.get('necessary_quantity_leads')
    status = data.get('status')
    update_tasks = data.get('update_tasks')

    # Получаем список всех сделок
    leads = list((await get_leads_by_filter_async(pipeline_id=pipeline_id, status=status)).keys())

    for i, user_id in enumerate(users_ids):
        target_leads_count = necessary_quantity_leads[i]

        if (i + 1) == len(users_ids):
            user_leads = leads
        else:
            user_leads = leads[:target_leads_count]
            leads = leads[target_leads_count:]

        await set_responsible_user_in_lead(user_leads, user_id)

        if update_tasks:
            await set_responsible_user_in_task_by_lead(user_leads, user_id)

    end = datetime.datetime.now()

    return {'status': 200,
            "time_process": (end - start),
            'data': {
                'users': users_ids,
                'percents': necessary_quantity_leads,
            }}


@router.patch("/allocation_all_leads_by_contacts")
async def allocation_all_leads_by_contacts(pipeline_id: int, status_id: int, update_tasks: bool):
    """Распределение всех сделок по контакту"""

    initialize_token()

    all_leads = await get_leads_by_filter_async(pipeline_id=pipeline_id, status=status_id)

    for lead, value in all_leads.items():
        responsible_user = await get_responsible_user_contact(value['contact_id'])
        await set_responsible_user_in_lead([lead], responsible_user)

        if update_tasks:
            await set_responsible_user_in_task_by_lead([lead], responsible_user)

    return {'status': 200,
            'data': {
                'leads': all_leads
            }}


@router.patch("/allocation_all_leads_by_company")
async def allocation_all_leads_by_companies(pipeline_id: int, status_id: int, update_tasks: bool):
    """Распределение всех сделок по компании"""

    initialize_token()

    all_leads = await get_leads_by_filter_async(pipeline_id=pipeline_id, status=status_id)

    for lead, value in all_leads.items():
        responsible_user = await get_responsible_user_company(value['company_id'])
        await set_responsible_user_in_lead([lead], responsible_user)

        if update_tasks:
            await set_responsible_user_in_task_by_lead([lead], responsible_user)


@router.patch("/config_widget")
async def config_widget(data: ConfigWidgetBody):
    """Настройка виджета (триггера)"""

    initialize_token()
    data = dict(data)

    mode = data.get('mode')
    use_contact = data.get('use_contact')  # Нет метода
    use_company = data.get('use_company')  # Нет метода
    accept_to_existing_leads = data.get('accept_to_existing_leads')
    pipeline_id = data.get('pipeline_id')
    users_ids = data.get('users_ids')
    percents = data.get('percents')
    status = data.get('status')

    if accept_to_existing_leads:

        # Основное распределение
        if mode == 'percent':
            await allocation_all_leads_by_percent(AllocationAllByPercentBody(**data))

        elif mode == 'max_count':
            await allocation_all_leads_by_max_count(AllocationAllByMaxCountBody(**data))

        else:
            return f'Неверно передан режим. Получено: {mode}'

        # Дополнительное распределение
        if use_company:
            await allocation_all_leads_by_companies(pipeline_id, status)

        if use_contact:
            await allocation_all_leads_by_contacts(pipeline_id, status)

    return f'/trigger_allocation?users={users_ids}&percents={percents}%use_contact={use_contact}'


@router.patch("/trigger_allocation")
async def trigger():
    pass


@router.patch("/integration")
async def trigger():
    pass


@router.get("/get")
async def get(client_id: str, subdomain: str, session: AsyncSession = Depends(get_async_session)):
    try:
        await initialize_token(client_id, subdomain, session)
        return {
            "status": "success",
            "message": None,
            "data": await get_analytics_by_pipeline(subdomain, session)
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
