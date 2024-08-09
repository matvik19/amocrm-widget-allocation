import logging

from typing import AsyncGenerator

from aiohttp import ClientSession
from fastapi import HTTPException

import json
from typing import List

import aiohttp
from amocrm.v2 import User, Lead

from src.config import *


async def get_client_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Асинхронная ссесия для запросов к амо"""

    async with aiohttp.ClientSession() as session:
        yield session


async def get_leads_by_filter_async(
    client_session: ClientSession,
    subdomain: str,
    headers: dict,
    pipeline_id: int,
    statuses_ids: List[int] = None,
    responsible_user_id: int = None,
) -> List[dict]:
    """Асинхронное получение сделок с помощью фильтра"""

    """
    FILTERS:
        filter[responsible_user_id] - по ответственному
        filter[pipeline_id] - по воронке
        filter[status][] - по статусам
    """

    params = {"filter[pipeline_id]": pipeline_id}
    if statuses_ids:
        for i, status_id in enumerate(statuses_ids):
            params[f"filter[status][{i}]"] = status_id
    if responsible_user_id:
        params["filter[responsible_user_id]"] = responsible_user_id

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads?with=contacts"

    try:
        async with client_session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                response_json = await response.json()

                # Извлекаем список сделок из ответа JSON
                leads = response_json.get("_embedded", {}).get("leads", [])
                return leads

            elif response.status == 204:
                logging.error(f"Error: {response.status} | Ответ получен без тела")
                return []
            else:
                error_message = await response.text()
                logging.error(f"Error: {response.status}, Message: {error_message}")
                raise HTTPException(
                    status_code=response.status, detail="Failed to fetch leads"
                )
    except Exception as e:
        logging.exception(f"Failed to fetch leads: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_lead_by_id(
    lead_id: int, subdomain: str, headers: dict, client_session: ClientSession
):
    """Получение объекта сделки по id сделки"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads/{lead_id}?with=contacts"

    try:
        async with client_session.get(url, headers=headers) as response:
            data = await response.json()
            return data

    except Exception as e:
        logging.exception(f"Failed to get lead with contacts: {e}")
        raise HTTPException(
            status_code=500, detail="Error getting lead contacts from server"
        )


async def get_contact_by_id(
    contact_id: int, subdomain: str, headers: dict, client_session: ClientSession
):
    """Получение объекта контакта по id контакта"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/contacts/{contact_id}"

    try:
        async with client_session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                logging.error(
                    f"Error: {response.status}, Message: {await response.text()}"
                )
                raise HTTPException(
                    status_code=response.status, detail="Failed to fetch contact"
                )
    except Exception as e:
        logging.exception(f"Failed to fetch contact by id: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch contact by id")


async def get_all_contacts(
    subdomain: str, headers: dict, client_session: ClientSession
):
    """Получение всех контактов"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/contacts"

    try:
        async with client_session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                contacts = []
                # Формируем список словарей содержащих id контакта и его ответственного
                for contact in data["_embedded"]["contacts"]:
                    contacts.append(
                        {
                            "id": contact["id"],
                            "responsible_user_id": contact["responsible_user_id"],
                        }
                    )
                return contacts
            else:
                logging.error(
                    f"Error: {response.status}, Message: {await response.text()}"
                )
                raise HTTPException(
                    status_code=response.status, detail="Failed to fetch contacts"
                )
    except Exception as e:
        logging.exception(f"Failed to fetch all contacts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch all contacts")


async def get_company_by_id(
    company_id: int, subdomain: str, headers: dict, client_session: ClientSession
):
    """Получение объкта компании по id"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/companies/{company_id}"

    try:
        async with client_session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                logging.error(
                    f"Error: {response.status}, Message: {await response.text()}"
                )
                raise HTTPException(
                    status_code=response.status, detail="Failed to fetch company"
                )
    except Exception as e:
        logging.exception(f"Failed to fetch company by id: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def set_responsible_user_in_lead(
    lead_id: int,
    responsible_user_id: int,
    subdomain: str,
    headers: dict,
    client_session: ClientSession,
):
    """Назначить ответственного в сделке"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads/{lead_id}"

    body = json.dumps({"responsible_user_id": responsible_user_id})
    try:
        async with client_session.patch(url, headers=headers, data=body) as response:
            if response.status not in [200, 204]:
                logging.error(
                    f"Error: {response.status}, Message: {await response.text()}"
                )
                raise HTTPException(
                    status_code=response.status,
                    detail="Failed to update responsible user in lead",
                )
    except Exception as e:
        logging.exception(f"Failed to update responsible user in lead: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update responsible user in lead"
        )


async def set_responsible_user_in_task_by_lead(
    lead_id: int,
    responsible_user_id: int,
    subdomain: str,
    headers: dict,
    client_session: ClientSession,
):
    """Назначить ответственного в задаче конкретной сделки"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/tasks"

    try:
        params = {"filter[entity_id]": lead_id, "filter[entity_type]": "leads"}
        async with client_session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                error_message = await response.text()
                logging.error(
                    f"Failed to fetch tasks for lead {lead_id}: {response.status} {error_message}"
                )
                raise HTTPException(
                    status_code=response.status, detail="Failed to fetch tasks for lead"
                )

            result_tasks = await response.json(content_type=None)
            task_ids = [
                task.get("id")
                for task in result_tasks.get("_embedded", {}).get("tasks", [])
            ]

        if not task_ids:
            logging.info(f"No tasks found for lead {lead_id}. No updates needed.")
            return None

        body = json.dumps(
            [
                {"id": task_id, "responsible_user_id": responsible_user_id}
                for task_id in task_ids
            ]
        )

        async with client_session.patch(url, headers=headers, data=body) as response:
            if response.status not in [200, 204]:
                error_message = await response.text()
                logging.error(
                    f"Error updating tasks for lead {lead_id}: {response.status} {error_message}"
                )
                raise HTTPException(
                    status_code=response.status,
                    detail="Failed to update responsible user in tasks",
                )
    except Exception as e:
        logging.exception(
            f"Failed to update responsible user in tasks for lead {lead_id}. Probably tasks are empty: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update responsible user in tasks. Probably tasks are empty",
        )


async def set_responsible_user_in_contact_by_lead(
    contact_id: int,
    responsible_user_id: int,
    subdomain: str,
    headers: dict,
    client_session: ClientSession,
):
    """Назначить ответственного за контакт"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/contacts/{contact_id}"

    body = json.dumps({"id": contact_id, "responsible_user_id": responsible_user_id})

    # Отправляем изменение в amoCRM
    try:
        async with client_session.patch(url, headers=headers, data=body) as response:
            if response.status not in [200, 204]:
                logging.error(
                    f"Error: {response.status}, Message: {await response.text()}"
                )
                raise HTTPException(
                    status_code=response.status,
                    detail="Failed to update responsible user in contact",
                )
    except Exception as e:
        logging.exception(
            f"Failed to update responsible user in contact. Probably contacts are empty: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update responsible user in contact. Probably contacts are empty",
        )


async def set_responsible_user_in_company_by_lead(
    company_id: int,
    responsible_user_id: int,
    subdomain: str,
    headers: dict,
    client_session: ClientSession,
):
    """Назначить ответственного за компанию"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/companies/{company_id}"

    body = json.dumps({"id": company_id, "responsible_user_id": responsible_user_id})

    # Отправляем изменение в amoCRM
    try:
        async with client_session.patch(url, headers=headers, data=body) as response:
            if response.status not in [200, 204]:
                logging.error(
                    f"Error: {response.status}, Message: {await response.text()}"
                )
                raise HTTPException(
                    status_code=response.status,
                    detail="Failed to update responsible user in company",
                )
    except Exception as e:
        logging.exception(
            f"Failed to update responsible user in company. Probably companies are empty: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update responsible user in company. Probably companies are empty",
        )


def get_my_employments():
    """Получение всех сотрудников"""

    return [emp for emp in User.objects.all() if emp.is_active]


def get_info_about_tasks_by_lead(lead: Lead):
    """Получение всей информации о задачах сделки"""

    tasks = lead.tasks
    print("ЗАДАЧИ")
    for t in tasks:
        print(f"ID: {t.id}")
        print(f"ОТВЕСТВЕННЫЙ: {t.responsible_user.name}")
        print(f"СОЗДАТЕЛЬ: {t.created_by.name}")
        print(f"ОБНОВИЛ: {t.updated_by.name}\n")


def print_employments():
    """Вывод все сотрудников"""

    print("Сотрудники")
    for emp in get_my_employments():
        print(emp.id, emp.name)


def give_all_tasks_to_responsible_user(new_responsible_user: User, lead: Lead):
    """Назначение всех задач сделки пользователю, ответственному за сделку"""

    for task in lead.tasks:
        task.responsible_user = new_responsible_user
        task.save()
