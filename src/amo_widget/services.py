import datetime
import logging
from typing import Tuple

from aiohttp import ClientSession

from .requests_amocrm import *
from .schemas import AllocationNewLeadByCompanyContacts


async def allocate_by_percent(
    data, user_leads_counts, all_leads_count, headers, client_session
):
    """Распределние по процентам с учетом максимального кол-ва"""

    subdomain = data.get("subdomain")
    lead_id = data.get("lead_id")
    users_ids = data.get("users_ids")
    percents = data.get("percents")
    max_counts = data.get("max_counts", [])

    for i, user_id in enumerate(users_ids):
        target_leads_count = int(all_leads_count * percents[i] / 100)
        max_count = max_counts[i] if i < len(max_counts) else None

        if (
            max_count is None or user_leads_counts[user_id] < max_count
        ) and user_leads_counts[user_id] < target_leads_count:
            await set_responsible_user_in_lead(
                lead_id, user_id, subdomain, headers, client_session
            )
            print("Закончили распределение по процентам")
            return {"status": 200, "lead": lead_id}

    return None


async def allocate_by_max_count(data, user_leads_counts, headers, client_session):
    """Распределние по максимальному кол-ву"""

    subdomain = data.get("subdomain")
    lead_id = data.get("lead_id")
    users_ids = data.get("users_ids")
    max_counts = data.get("max_counts", [])

    for i, user_id in enumerate(users_ids):
        max_count = max_counts[i] if i < len(max_counts) else None

        if max_count is None or user_leads_counts[user_id] < max_count:
            await set_responsible_user_in_lead(
                lead_id, user_id, subdomain, headers, client_session
            )
            print("Закончили распределение по максимальному количеству")
            return {"status": 200, "lead": lead_id}

    return None


async def allocation_new_lead_by_percent_or_max_count(
    data: dict, headers: dict, client_session: ClientSession
):
    """Распределение новой сделки по процентам и максимальному количеству"""

    try:
        subdomain = data.get("subdomain")
        users_ids = data.get("users_ids")
        pipelines_statuses = data.get("pipelines_statuses", {})
        default_status_id = data.get("status_id")
        default_pipeline_id = data.get("pipeline_id")

        all_leads_count = 0
        user_leads_counts = {user_id: 0 for user_id in users_ids}

        if pipelines_statuses:
            print("Воронки и статусы: ", pipelines_statuses)
            # Считаем количество сделок по каждой воронке и статусу из pipelines_statuses
            for pipeline_id, statuses_ids in pipelines_statuses.items():
                print("Считаем сделки на воронке с id: ", pipeline_id)
                print("Статусы которые нам пришли id: ", statuses_ids)

                # Получаем все сделки для текущей воронки и статусов
                leads = await get_leads_by_filter_async(
                    client_session,
                    subdomain,
                    headers,
                    pipeline_id=pipeline_id,
                    statuses_ids=statuses_ids,
                )
                print(
                    f"Список сделок в воронке с id {pipeline_id} со статусами {statuses_ids}||: {leads}"
                )
                print("***********************************************")
                all_leads_count += len(leads)
                print(
                    f"Количество сделок на этапах {statuses_ids} в воронке {pipeline_id}: {all_leads_count}"
                )

                # Получаем количество сделок для пользователей по текущей воронке и статусам
                user_leads_counts_in_pipeline_with_statuses = (
                    await get_user_leads_counts(
                        users_ids,
                        pipeline_id,
                        subdomain,
                        headers,
                        client_session,
                        statuses_ids,
                    )
                )
                print(
                    f"Пользователи {users_ids}, имеют сделок на {pipeline_id}:"
                    f"{user_leads_counts_in_pipeline_with_statuses}"
                )

                # Обновляем общее количество сделок для пользователей
                for (
                    user_id,
                    count,
                ) in user_leads_counts_in_pipeline_with_statuses.items():
                    user_leads_counts[user_id] += count

                print(
                    f"Обновленное количество сдeлок для пользователя: {user_leads_counts}"
                )
        else:
            print("ЗАШЛИ В ELSE!!!")
            # Получаем все сделки для одной воронки и одного статуса
            leads = await get_leads_by_filter_async(
                client_session,
                subdomain,
                headers,
                pipeline_id=default_pipeline_id,
                statuses_ids=[default_status_id],
            )
            all_leads_count = len(leads)

            # Получаем количество сделок для пользователей по одной воронке и одному статусу
            user_leads_counts = await get_user_leads_counts(
                users_ids,
                default_pipeline_id,
                subdomain,
                headers,
                client_session,
                [default_status_id],
            )
            print("user_leads_counts", user_leads_counts)

        print(f"Total leads count: {all_leads_count}")
        print(f"User leads counts: {user_leads_counts}")

        # Попытка распределения по процентам
        allocation_result = await allocate_by_percent(
            data,
            user_leads_counts,
            all_leads_count,
            headers,
            client_session,
        )

        if allocation_result:
            return allocation_result

        # Попытка распределения по максимальному количеству
        allocation_result = await allocate_by_max_count(
            data,
            user_leads_counts,
            headers,
            client_session,
        )

        if allocation_result:
            return allocation_result

    except Exception as e:
        logging.exception(
            "Error when trying to distribute a deal by maximum quantity or percentage"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error when trying to distribute a deal by maximum quantity or percentage: {str(e)}",
        )


async def allocation_new_lead_by_contacts(
    data: AllocationNewLeadByCompanyContacts,
    headers: dict,
    client_session: ClientSession,
):
    """Распределение сделки по контакту"""

    lead = await get_lead_by_id(data.lead_id, data.subdomain, headers, client_session)
    contacts_lead = lead["_embedded"]["contacts"]

    if contacts_lead:
        contact_id = lead["_embedded"]["contacts"][0]["id"]
        contact_lead = await get_contact_by_id(
            contact_id, data.subdomain, headers, client_session
        )
        responsible_user_of_contact = contact_lead["responsible_user_id"]

        await set_responsible_user_in_lead(
            data.lead_id,
            responsible_user_of_contact,
            data.subdomain,
            headers,
            client_session,
        )
    else:
        return None


async def allocation_new_lead_by_company(
    data: AllocationNewLeadByCompanyContacts,
    headers: dict,
    client_session: ClientSession,
):
    """Распределение сделки по компании"""

    lead = await get_lead_by_id(data.lead_id, data.subdomain, headers, client_session)

    if lead["_embedded"]["companies"]:
        company_id = lead["_embedded"]["companies"][0]["id"]
        company = await get_company_by_id(
            company_id, data.subdomain, headers, client_session
        )

        await set_responsible_user_in_lead(
            data.lead_id,
            company["responsible_user_id"],
            data.subdomain,
            headers,
            client_session,
        )
    else:
        return None


async def get_info_about_lead_contact(
    data: dict, headers: dict, client_session: ClientSession
):
    """Получить информацию о контакте сделки"""

    try:
        lead_id = data.get("lead_id")
        subdomain = data.get("subdomain")

        lead = await get_lead_by_id(lead_id, subdomain, headers, client_session)

        contact = lead["_embedded"]["contacts"]
        if not contact:
            raise ValueError("No contacts found in lead")

        contact_lead = await get_contact_by_id(
            contact[0]["id"], subdomain, headers, client_session
        )

        return contact[0]["id"], contact_lead

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logging.exception(f"Failed to get info about contact lead: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def allocation_new_lead_by_contact_company(
    data: dict, headers: dict, client_session: ClientSession
):
    """Объединение распределений в зависимости от настроек полученных с триггера"""
    try:
        contact_id, contact_lead = await get_info_about_lead_contact(
            data, headers, client_session
        )

        if data.get("ignore_manager") == contact_lead["responsible_user_id"]:
            print("Прошли условие ignore_manager")
            if data.get("percents") or data.get("max_counts"):
                print("Зашли в конкретное распределение")
                await allocation_new_lead_by_percent_or_max_count(
                    data, headers, client_session
                )
            else:
                await default_allocation_by_schedule(data, headers, client_session)
        else:
            await allocate_lead_by_company_or_contacts(data, headers, client_session)

        await update_responsible_in_dependent_entities(
            data, contact_id, headers, client_session
        )
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        logging.exception("Error in allocation_new_lead_by_contact_company")
        raise HTTPException(status_code=500, detail=str(e))


async def allocation_new_lead(data: dict, headers: dict, client_session: ClientSession):
    """Распределение по мнедежрам из таблицы распределения (если она есть), либо из графика"""
    contact_id, contact_lead = await get_info_about_lead_contact(
        data, headers, client_session
    )

    if data.get("max_counts"):
        await allocation_new_lead_by_percent_or_max_count(data, headers, client_session)
    else:
        await default_allocation_by_schedule(data, headers, client_session)

    await update_responsible_in_dependent_entities(
        data, contact_id, headers, client_session
    )


async def default_allocation_by_schedule(
    data: dict, headers: dict, client_session: ClientSession
):
    """Распределение новой сделки в равных долях между пользователями из графика"""

    subdomain = data.get("subdomain")
    lead_id = data.get("lead_id")
    schedule = data.get("schedule")
    status_id_lead = data.get("status_id")
    pipeline_id = data.get("pipeline_id")

    lead = await get_lead_by_id(lead_id, subdomain, headers, client_session)
    contact_id = lead["_embedded"]["contacts"][0]["id"]
    user_leads_counts = await get_user_leads_counts(
        schedule, pipeline_id, subdomain, headers, client_session, [status_id_lead]
    )

    user_id = min(user_leads_counts, key=user_leads_counts.get)

    await set_responsible_user_in_lead(
        lead_id, user_id, subdomain, headers, client_session
    )

    await update_responsible_in_dependent_entities(
        data, contact_id, headers, client_session
    )

    return {
        "status": 200,
        "lead": lead_id,
        "assigned_to": user_id,
    }


async def get_user_leads_counts(
    users_ids: list,
    pipeline_id: int,
    subdomain: str,
    headers: dict,
    client_session: ClientSession,
    statuses_ids: List[int] = None,
):
    """Получение кол-ва сделок пользователя на конкретном этапе"""

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
        print(user_leads)
        user_leads_counts[user_id] = len(user_leads)
    return user_leads_counts


async def update_responsible_in_dependent_entities(
    data: dict,
    contact_id: int,
    headers: dict,
    client_session: ClientSession,
):
    """Ответсвенный за сделку назначается ответсвенным за определенные сущности, которые пришли из триггера"""

    lead_id = data.get("lead_id")
    subdomain = data.get("subdomain")

    lead = await get_lead_by_id(lead_id, subdomain, headers, client_session)

    if data.get("update_contacts"):
        await set_responsible_user_in_contact_by_lead(
            contact_id,
            lead["responsible_user_id"],
            subdomain,
            headers,
            client_session,
        )

    if data.get("update_companies"):
        if lead["_embedded"]["companies"]:
            await set_responsible_user_in_company_by_lead(
                company_id=lead["_embedded"]["companies"][0]["id"],
                responsible_user_id=lead["responsible_user_id"],
                subdomain=subdomain,
                headers=headers,
                client_session=client_session,
            )

    if data.get("update_tasks"):
        await set_responsible_user_in_task_by_lead(
            lead_id=lead_id,
            responsible_user_id=lead["responsible_user_id"],
            subdomain=subdomain,
            headers=headers,
            client_session=client_session,
        )


async def allocate_lead_by_company_or_contacts(
    data: dict, headers: dict, client_session: ClientSession
):
    """Распределить сделку по компании(если есть) или по контакту(если нет компании)"""

    allocation_result = await allocation_new_lead_by_company(
        AllocationNewLeadByCompanyContacts(**data), headers, client_session
    )

    if allocation_result is None:
        await allocation_new_lead_by_contacts(
            AllocationNewLeadByCompanyContacts(**data), headers, client_session
        )
