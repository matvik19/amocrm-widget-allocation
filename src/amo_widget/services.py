import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import *
from src.amo_widget.token_init import initialize_token
from .utils import *
from ..database import get_async_session


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


async def allocation_new_lead_by_company(data: AllocationNewLeadByCompany, headers: dict):
    """Распределение новой сделки по компании"""

    company_id = await get_company_by_lead(data.lead_id)

    if company_id:
        responsible_user = await get_responsible_user_company(company_id, data.subdomain, headers)
    else:
        return {
            'status': 400,
            'lead': data.lead_id
        }

    await set_responsible_user_in_lead([data.lead_id], responsible_user, data.subdomain, headers)

    if data.update_tasks:
        await set_responsible_user_in_task_by_lead([data.lead_id], responsible_user,
                                                   data.subdomain, headers)


async def allocation_all_leads_by_percent(
        data: AllocationAllByPercentBody, headers: dict
):
    """Распределение по процентам всех сделок в этапе"""

    start = datetime.datetime.now()

    # Получаем список всех сделок
    leads = list((await get_leads_by_filter_async(data.subdomain, headers, data.pipeline_id, data.status_id)).keys())

    for i, user_id in enumerate(data.users_ids):
        target_leads_count = int(len(leads) * data.percents[i] / 100)

        if (i + 1) == len(data.users_ids):
            user_leads = leads
        else:
            user_leads = leads[:target_leads_count]
            leads = leads[target_leads_count:]

        await set_responsible_user_in_lead(user_leads, user_id, data.subdomain, headers)

        if data.update_tasks:
            await set_responsible_user_in_task_by_lead(user_leads, user_id, data.subdomain, headers)

    end = datetime.datetime.now()


async def allocation_all_leads_by_max_count(data: AllocationAllByMaxCountBody, headers: dict):
    """Распределение всех сделок по максимальному количеству"""

    start = datetime.datetime.now()

    # Получаем список всех сделок
    leads = list((await get_leads_by_filter_async(data.subdomain, headers, data.pipeline_id, data.status_id)).keys())

    for i, user_id in enumerate(data.users_ids):
        target_leads_count = data.necessary_quantity_leads[i]

        if (i + 1) == len(data.users_ids):
            user_leads = leads
        else:
            user_leads = leads[:target_leads_count]
            leads = leads[target_leads_count:]

        await set_responsible_user_in_lead(user_leads, user_id, data.subdomain, headers)

        if data.update_tasks:
            await set_responsible_user_in_task_by_lead(user_leads, user_id, data.subdomain, headers)

    end = datetime.datetime.now()


async def allocation_all_leads_by_contacts(data: AllocationAllByCompanyContacts, headers: dict):
    """Распределение всех сделок по контакту"""

    all_leads = await get_leads_by_filter_async(data.subdomain, headers, data.pipeline_id, data.status_id)

    for lead, value in all_leads.items():
        responsible_user = await get_responsible_user_contact(value['contact_id'], headers, data.subdomain)
        await set_responsible_user_in_lead([lead], responsible_user, data.subdomain, headers)

        if data.update_tasks:
            await set_responsible_user_in_task_by_lead([lead], responsible_user, data.subdomain, headers)


async def allocation_all_leads_by_companies(data: AllocationAllByCompanyContacts, headers: dict):
    """Распределение всех сделок по компании"""

    all_leads = await get_leads_by_filter_async(data.subdomain, headers, data.pipeline_id, data.status_id)

    for lead, value in all_leads.items():
        responsible_user = await get_responsible_user_company(value['company_id'], data.subdomain, headers)
        await set_responsible_user_in_lead([lead], responsible_user, data.subdomain, headers)

        if data.update_tasks:
            await set_responsible_user_in_task_by_lead([lead], responsible_user, data.subdomain, headers)
