import datetime
from typing import Tuple

from aiohttp import ClientSession
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import *
from src.amo_widget.token_init import initialize_token
from .utils import *
from ..database import get_async_session


async def get_user_leads_counts(
    users_ids: list,
    pipeline_id: int,
    subdomain: str,
    headers: dict,
    client_session: ClientSession,
    statuses_ids: List[int] = None,
):
    """Получение кол-ва сделок пользователя"""
    user_leads_counts = {}
    for user_id in users_ids:
        user_leads = await get_leads_by_filter_async(
            client_session,
            subdomain,
            headers,
            pipeline_id=pipeline_id,
            statuses_ids=statuses_ids,
            responsible_user_id=user_id,
        )
        user_leads_counts[user_id] = len(user_leads)
    return user_leads_counts


async def allocation_new_lead_by_percent_or_max_count(
    data: dict, subdomain: str, headers: dict, client_session: ClientSession
):
    """Распределение новой сделки по процентам и максимальному количеству"""
    print("Распределяем сделку по проценту")
    lead_id = data.get("lead_id")
    users_ids = data.get("users_ids")
    percents = data.get("percents")
    max_counts = data.get("max_counts", [])
    statuses_ids = data.get("statuses_ids", [])
    status_id_lead = data.get("status_id")
    pipeline_id = data.get("pipeline_id")
    print("ПРОЦЕНТЫ", percents)
    update_tasks = data.get("update_tasks")

    all_leads = list(
        (
            await get_leads_by_filter_async(
                client_session,
                subdomain,
                headers,
                pipeline_id=pipeline_id,
                statuses_ids=[status_id_lead],
            )
        ).keys()
    )
    all_leads_count = len(all_leads)

    user_leads_counts = await get_user_leads_counts(
        users_ids, pipeline_id, subdomain, headers, client_session, statuses_ids
    )
    for i, user_id in enumerate(users_ids):
        target_leads_count = int(all_leads_count * percents[i] / 100)
        max_count = max_counts[i] if i < len(max_counts) else None
        print("Распределяем по первому for")
        # Проверяем возможность назначения новой сделки пользователю
        if (
            max_count is None or user_leads_counts[user_id] < max_count
        ) and user_leads_counts[user_id] < target_leads_count:
            await set_responsible_user_in_lead(
                [lead_id], user_id, subdomain, headers, client_session
            )

            if update_tasks:
                await set_responsible_user_in_task_by_lead(
                    [lead_id], user_id, subdomain, headers, client_session
                )

            print("Закончили распределение")

            return {
                "status": 200,
                "lead": lead_id,
            }

    for i, user_id in enumerate(users_ids):
        max_count = max_counts[i] if i < len(max_counts) else None

        if max_count is None or user_leads_counts[user_id] < max_count:
            await set_responsible_user_in_lead(
                [lead_id], user_id, subdomain, headers, client_session
            )

            if update_tasks:
                await set_responsible_user_in_task_by_lead(
                    [lead_id], user_id, subdomain, headers, client_session
                )

            return {
                "status": 200,
                "lead": lead_id,
            }

    return {
        "status": 400,
        "message": "Сделка не распределена. Не найден подходящий пользователь",
    }


async def allocation_new_lead_by_contacts(
    data: AllocationNewLeadByCompanyContacts,
    headers: dict,
    client_session: ClientSession,
):
    """Распределение новой сделки по контакту"""

    ignore_manager = data.ignore_manager

    contact_id_of_lead = await get_lead_with_contact_id(
        data.lead_id, data.subdomain, headers, client_session
    )

    if contact_id_of_lead:
        responsible_user_of_contact = await get_responsible_user_contact(
            contact_id_of_lead, headers, data.subdomain, client_session
        )
        if responsible_user_of_contact == ignore_manager:
            return
    else:
        return None

    await set_responsible_user_in_lead(
        [data.lead_id],
        responsible_user_of_contact,
        data.subdomain,
        headers,
        client_session,
    )

    if data.update_tasks:
        await set_responsible_user_in_task_by_lead(
            [data.lead_id],
            responsible_user_of_contact,
            data.subdomain,
            headers,
            client_session,
        )

    return {
        "status": 200,
        "lead": data.lead_id,
    }


async def allocation_new_lead_by_company(
    data: AllocationNewLeadByCompanyContacts,
    headers: dict,
    client_session: ClientSession,
):
    """Распределение новой сделки по компании"""

    company_id = await get_lead_with_company_by_id(
        data.lead_id, data.subdomain, headers, client_session
    )

    if company_id is None:
        return

    if company_id:
        responsible_user = await get_responsible_user_company(
            company_id, data.subdomain, headers, client_session
        )
    else:
        return {"status": 400, "lead": data.lead_id}

    await set_responsible_user_in_lead(
        [data.lead_id], responsible_user, data.subdomain, headers, client_session
    )

    if data.update_tasks:
        await set_responsible_user_in_task_by_lead(
            [data.lead_id], responsible_user, data.subdomain, headers, client_session
        )


async def allocation_new_lead(
    data: dict, subdomain: str, headers: dict, client_session: ClientSession
):

    update_contacts = data.get("update_contacts")
    update_companies = data.get("update_companies")
    ignore_manager = data.get("ignore_manager")
    update_tasks = data.get("update_contacts")
    lead_id = data.get("lead_id")

    contact_id = await get_lead_with_contact_id(
        lead_id, subdomain, headers, client_session
    )
    lead_contact = await get_contact_by_id(
        contact_id, subdomain, headers, client_session
    )

    if ignore_manager:
        if ignore_manager == lead_contact["responsible_user_id"]:
            await allocation_new_lead_by_percent_or_max_count(
                data, subdomain, headers, client_session
            )
            lead = await get_lead_by_id(lead_id, subdomain, headers, client_session)

            if update_contacts:
                await set_responsible_user_in_contact_by_lead(
                    contact_id=contact_id,
                    responsible_user_id=lead["responsible_user_id"],
                    subdomain=subdomain,
                    headers=headers,
                    client_session=client_session,
                )

            if update_companies:
                print("Меняем отвествеенного в компании")
                await set_responsible_user_in_company_by_lead(
                    company_id=lead["_embedded"]["companies"][0]["id"],
                    responsible_user_id=lead["responsible_user_id"],
                    subdomain=subdomain,
                    headers=headers,
                    client_session=client_session,
                )

            if update_tasks:
                await set_responsible_user_in_task_by_lead(
                    lead_ids=[lead_id],
                    responsible_user_id=lead["responsible_user_id"],
                    subdomain=subdomain,
                    headers=headers,
                    client_session=client_session,
                )
        else:
            await allocation_new_lead_by_contacts(
                AllocationNewLeadByCompanyContacts(**data), headers, client_session
            )
    else:
        print("Это мы в ELSE")
        await allocation_new_lead_by_percent_or_max_count(
            data, subdomain, headers, client_session
        )
