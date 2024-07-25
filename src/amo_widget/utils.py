import logging

import pytz
from typing import AsyncGenerator
from aiohttp import ClientSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from datetime import datetime, timedelta

from src.users.models import Users
import json
from typing import List

import aiohttp
import requests
from amocrm.v2 import User, Lead, Pipeline, Status, Contact
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import *


async def get_client_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    async with aiohttp.ClientSession() as session:
        yield session


async def get_leads_by_filter_async(
    client_session: ClientSession,
    subdomain: str,
    headers: dict,
    pipeline_id: int,
    statuses_ids: List[int] = None,
    responsible_user_id: int = None,
) -> dict:
    """Асинхронное получение сделок с помощью фильтра"""

    """
    FILTERS:
        filter[responsible_user_id] - по ответственному
        filter[pipeline_id] - по воронке
        filter[statuses][] - по статусам
    """

    params = {"filter[pipeline_id]": pipeline_id}
    if statuses_ids:
        for i, status_id in enumerate(statuses_ids):
            params[f"filter[statuses][{i}]"] = status_id
    if responsible_user_id:
        params["filter[responsible_user_id]"] = responsible_user_id

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads?with=contacts"

    try:
        async with client_session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                result_leads = {}
                response_json = await response.json()
                for lead_json in response_json["_embedded"]["leads"]:
                    contacts = lead_json.get("_embedded", {}).get("contacts", [])
                    companies = lead_json.get("_embedded", {}).get("companies", [])
                    contact_id = contacts[0].get("id") if contacts else None
                    company_id = companies[0].get("id") if companies else None

                    result_leads[lead_json.get("id")] = {
                        "contact_id": contact_id,
                        "company_id": company_id,
                    }
                return result_leads

            elif response.status == 204:
                logging.error(f"Error: {response.status} | Ответ получен без тела")
                return {}
            else:
                error_message = await response.text()
                logging.error(f"Error: {response.status}, Message: {error_message}")
                raise HTTPException(
                    status_code=response.status, detail="Failed to fetch leads"
                )
    except Exception as e:
        logging.exception(f"Failed to fetch leads: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# async def get_leads_by_filter_async(
#     client_session: ClientSession,
#     subdomain: str,
#     headers: dict,
#     pipeline_id: int,
#     status_id: int = None,
#     responsible_user_id: int = None,
# ) -> dict:
#     """Асинхронное получение сделок с помощью фильтра"""
#
#     """
#     FILTERS:
#         filter[responsible_user_id] - по ответственному
#         filter[pipeline_id] - по воронке
#         filter[status] - по статусу
#     """
#
#     params = {"filter[pipeline_id]": pipeline_id}
#     if status_id:
#         params["filter[status]"] = status_id
#     if responsible_user_id:
#         params["filter[responsible_user_id]"] = responsible_user_id
#
#     url = f"https://{subdomain}.amocrm.ru/api/v4/leads?with=contacts"
#
#     try:
#         async with client_session.get(url, params=params, headers=headers) as response:
#             if response.status == 200:
#                 result_leads = {}
#                 response_json = await response.json()
#                 for lead_json in response_json["_embedded"]["leads"]:
#                     contacts = lead_json.get("_embedded", {}).get("contacts", [])
#                     companies = lead_json.get("_embedded", {}).get("companies", [])
#                     contact_id = contacts[0].get("id") if contacts else None
#                     company_id = companies[0].get("id") if companies else None
#
#                     result_leads[lead_json.get("id")] = {
#                         "contact_id": contact_id,
#                         "company_id": company_id,
#                     }
#                 return result_leads
#
#             elif response.status == 204:
#                 logging.error(f"Error: {response.status} | Ответ получен без тела")
#                 return {}
#             else:
#                 error_message = await response.text()
#                 logging.error(f"Error: {response.status}, Message: {error_message}")
#                 raise HTTPException(
#                     status_code=response.status, detail="Failed to fetch leads"
#                 )
#     except Exception as e:
#         logging.exception(f"Failed to fetch leads: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")


async def get_lead_by_id(
    lead_id: int, subdomain: str, headers: dict, client_session: ClientSession
):
    """Получение объекта сделки по id сделки"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads/{lead_id}"

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
                    status_code=response.status, detail="Failed to fetch lead"
                )
    except Exception as e:
        logging.exception(f"Failed to fetch lead by id: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_lead_with_contact_id(
    lead_id: int, subdomain: str, headers: dict, client_session: ClientSession
):
    """Получение контактов сделки по id сделки"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads/{lead_id}?with=contacts"

    try:
        async with client_session.get(url, headers=headers) as response:
            data = await response.json()
            if data["_embedded"]["contacts"]:
                contact_id = data["_embedded"]["contacts"][0]["id"]
            else:
                contact_id = None
            return contact_id

    except Exception as e:
        logging.exception(f"Failed to get lead with contacts: {e}")
        raise HTTPException(
            status_code=500, detail="Error getting lead contacts from server"
        )


async def get_contact_by_id(
    contact_id: int, subdomain: str, headers: dict, client_session: ClientSession
):
    """Получение объекта контакта по айди контакта"""

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


async def get_responsible_user_contact(
    contact_id: int, headers: dict, subdomain: str, client_session: ClientSession
):
    """Получение ответственного контакта по id"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/contacts/{contact_id}"

    try:
        async with client_session.get(url, headers=headers) as response:
            data = await response.json()
            return data["responsible_user_id"]
    except Exception as e:
        logging.exception(f"Failed to get responsible user contact: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get responsible user contact"
        )


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


async def get_lead_with_company_by_id(
    lead_id: int, subdomain: str, headers: dict, client_session: ClientSession
):
    """Получение компаний сделки по id сделки"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads/{lead_id}?with=companies"

    try:
        async with client_session.get(url, headers=headers) as response:
            data = await response.json()
            print("КОМПАНИИ", data)
            if data["_embedded"]["companies"]:
                company_id = data["_embedded"]["companies"][0]["id"]
            else:
                company_id = None
            return company_id

    except Exception as e:
        logging.exception(f"Failed to get lead with company: {e}")
        raise HTTPException(
            status_code=500, detail="Error getting lead company from server"
        )


async def get_company_by_id(
    company_id: int, subdomain: str, headers: dict, client_session: ClientSession
):
    """Получение объкта компании по айди"""

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


async def get_responsible_user_company(
    company_id: int, subdomain: str, headers: dict, client_session: ClientSession
):
    """Получение ответственного компании по id"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/companies/{company_id}"

    try:
        async with client_session.get(url, headers=headers) as response:
            data = await response.json()
            return data["responsible_user_id"]
    except Exception as e:
        logging.exception(f"Failed to get responsible user company: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def set_responsible_user_in_lead(
    lead_ids: list,
    responsible_user_id: int,
    subdomain: str,
    headers: dict,
    client_session: ClientSession,
):
    """Изменение ответственного в сделках по списку сделок"""
    url = f"https://{subdomain}.amocrm.ru/api/v4/leads"

    # Генерируем список с новым ответственным в сделках
    body = json.dumps(
        [
            {
                "id": lead_id,
                "responsible_user_id": responsible_user_id,
            }
            for lead_id in lead_ids
        ]
    )

    # Отправляем изменение в amoCRM
    try:
        async with client_session.patch(url, headers=headers, data=body) as response:
            if response.status not in [200, 204]:
                logging.error(
                    f"Error: {response.status}, Message: {await response.text()}"
                )
                raise HTTPException(
                    status_code=response.status,
                    detail="Failed to update responsible user in leads",
                )
    except Exception as e:
        logging.exception(f"Failed to update responsible user in leads: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def set_responsible_user_in_task_by_lead(
    lead_ids: list,
    responsible_user_id: int,
    subdomain: str,
    headers: dict,
    client_session: ClientSession,
):
    """Изменение ответственного в задачах по списку сделок"""
    url = f"https://{subdomain}.amocrm.ru/api/v4/tasks"

    task_ids = []

    try:
        for lead_id in lead_ids:
            params = {"filter[entity_id]": lead_id, "filter[entity_type]": "leads"}

            async with client_session.get(
                url, headers=headers, params=params
            ) as response:
                result_tasks = await response.json(content_type=None)

                if result_tasks is None:
                    continue

                for task_json in result_tasks["_embedded"]["tasks"]:
                    task_ids.append(task_json.get("id"))

        if not task_ids:
            return None

        body = json.dumps(
            [
                {
                    "id": task_id,
                    "responsible_user_id": responsible_user_id,
                }
                for task_id in task_ids
            ]
        )

        async with client_session.patch(url, headers=headers, data=body) as response:
            if response.status not in [200, 204]:
                logging.error(
                    f"Error: {response.status}, Message: {await response.text()}"
                )
                raise HTTPException(
                    status_code=response.status,
                    detail="Failed to update responsible user in tasks",
                )
    except Exception as e:
        logging.exception(f"Failed to update responsible user in tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def set_responsible_user_in_contact_by_lead(
    contact_id: int,
    responsible_user_id: int,
    subdomain: str,
    headers: dict,
    client_session: ClientSession,
):
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
        logging.exception(f"Failed to update responsible user in contact: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update responsible user in contact"
        )


async def set_responsible_user_in_company_by_lead(
    company_id: int,
    responsible_user_id: int,
    subdomain: str,
    headers: dict,
    client_session: ClientSession,
):
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
                    detail="Failed to update responsible user in contact",
                )
    except Exception as e:
        logging.exception(f"Failed to update responsible user in contact: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update responsible user in contact"
        )


async def get_tokens_from_db(subdomain: str, session: AsyncSession):
    """Запрос на получение токенов пользователя из базы данных"""

    query = select(Users.access_token, Users.refresh_token).filter_by(
        subdomain=subdomain
    )
    result = await session.execute(query)
    tokens_from_db = result.first()

    if not tokens_from_db:
        raise ValueError("Tokens not found")

    return tokens_from_db


async def get_headers(subdomain: str, access_token: str):
    """Получение headers для запросов"""

    headers = {
        "Host": subdomain + ".amocrm.ru",
        "Content - Length": "0",
        "Content - Type": "application / json",
        "Authorization": "Bearer " + access_token,
    }

    return headers


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
