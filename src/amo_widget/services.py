import datetime

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
):
    """Получение кол-ва сделок пользователя"""
    user_leads_counts = {}
    for user_id in users_ids:
        user_leads = await get_leads_by_filter_async(
            client_session,
            subdomain,
            headers,
            pipeline_id=pipeline_id,
            responsible_user_id=user_id,
        )
        user_leads_counts[user_id] = len(user_leads)
    return user_leads_counts


async def allocation_new_lead(
    data: dict, subdomain: str, headers: dict, client_session: ClientSession
):
    """Распределение новой сделки по процентам и максимальному количеству"""
    print("Распределяем сделку по проценту")
    lead_id = data.get("lead_id")
    users_ids = data.get("users_ids")
    percents = data.get("percents")
    max_counts = data.get("max_counts", [])
    statuses_id = data.get("statuses_id", [])
    print("ПРОЦЕНТЫ", percents)
    update_tasks = data.get("update_tasks")

    lead_to_allocate = await get_lead_by_id(lead_id, subdomain, headers, client_session)
    status_id = lead_to_allocate.get("status_id")
    pipeline_id = lead_to_allocate.get("pipeline_id")

    all_leads = list(
        (
            await get_leads_by_filter_async(
                client_session,
                subdomain,
                headers,
                pipeline_id=pipeline_id,
                status_id=status_id,
            )
        ).keys()
    )
    all_leads_count = len(all_leads)

    user_leads_counts = await get_user_leads_counts(
        users_ids, pipeline_id, subdomain, headers, client_session
    )

    for i, user_id in enumerate(users_ids):
        target_leads_count = int(all_leads_count * percents[i] / 100)
        max_count = max_counts[i] if i < len(max_counts) else None

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

    contact_id_of_lead = await get_lead_with_contact_id(
        data.lead_id, data.subdomain, headers, client_session
    )

    if contact_id_of_lead is None:
        return

    lead_contact = await get_contact_by_id(
        contact_id_of_lead, data.subdomain, headers, client_session
    )
    created_at = lead_contact.get("created_at")
    print("Время создания контакта", created_at)

    if is_timestamp_within_range(created_at):
        print("Контакт новый, создался только что. Вышли из распределения")
        return

    if contact_id_of_lead:
        print("Контакт старый(уже был в базе) начали распределение по контакту")
        responsible_user_of_contact = await get_responsible_user_contact(
            contact_id_of_lead, headers, data.subdomain, client_session
        )

    else:
        return {
            "status": 400,
            "lead": data.lead_id,
        }

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

    lead_company = await get_company_by_id(
        company_id, data.subdomain, headers, client_session
    )
    created_at = lead_company.get("created_at")
    print("Время создания компании", created_at)

    if is_timestamp_within_range(created_at):
        print("Компания новая, создалась только что. Вышли из распределения")
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
