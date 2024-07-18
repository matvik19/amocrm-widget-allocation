from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.users.models import Users
import json
from typing import List

import aiohttp
import requests
from amocrm.v2 import User, Lead, Pipeline, Status, Contact
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import *

client_session = aiohttp.ClientSession()


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


async def get_analytics_by_pipeline(subdomain: str, session: AsyncSession):
    """Получение аналитики по воронке"""

    leads_andrey = await get_leads_by_filter_async(
        subdomain,
        headers,
        responsible_user_id=5837446,
        pipeline_id=8319714,
        status_id=67829730,
    )
    leads_dmitry = await get_leads_by_filter_async(
        subdomain,
        session,
        responsible_user_id=9606738,
        pipeline_id=8319714,
        status=67829730,
    )
    leads_in_pipeline = await get_leads_by_filter_async(
        subdomain, session, pipeline_id=8319714, status=67829730
    )

    print("ВСЕГО СДЕЛОК:", len(leads_in_pipeline))
    print("СДЕЛОК У АНДРЕЯ:", len(leads_andrey))
    print("СДЕЛОК У ДМИТРИЯ:", len(leads_dmitry))


async def get_leads_by_filter_async(
    subdomain: str,
    headers: dict,
    pipeline_id: int,
    status_id: int = None,
    responsible_user_id: int = None,
) -> dict:
    """Асинхронное получение сделок с помощью фильтра"""

    """
    FILTERS:
        filter[responsible_user_id] - по ответственному
        filter[pipeline_id] - по воронке
        filter[status] - по статусу
    """

    params = {"filter[pipeline_id]": pipeline_id}
    if status_id:
        params["filter[status]"] = status_id
    if responsible_user_id:
        params["filter[responsible_user_id]"] = responsible_user_id

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads?with=contacts"

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
            print(f"Error: {response.status} | Ответ получен без тела")
            return {}
        else:
            print(f"Error: {response.status}")
            return {}


async def set_responsible_user_in_lead(
    lead_ids: list, responsible_user_id: int, subdomain: str, headers: dict
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
    await client_session.patch(url, headers=headers, data=body)


async def set_responsible_user_in_task_by_lead(
    lead_ids: list, responsible_user_id: int, subdomain: str, headers: dict
):
    """Изменение ответственного в задачах по списку сделок"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/tasks"

    task_ids = []

    # Достаем id всех задач из переданных сделок
    for lead_id in lead_ids:
        params = {"filter[entity_id]": lead_id, "filter[entity_type]": "leads"}

        async with client_session.get(url, headers=headers, params=params) as response:
            result_tasks = await response.json(content_type=None)

            if result_tasks is None:
                continue

            for task_json in result_tasks["_embedded"]["tasks"]:
                task_ids.append(task_json.get("id"))

    # Генерируем список с новым ответственным в задачах
    body = json.dumps(
        [
            {
                "id": task_id,
                "responsible_user_id": responsible_user_id,
            }
            for task_id in task_ids
        ]
    )

    # Отправляем изменение в amoCRM
    await client_session.patch(url, headers=headers, data=body)


async def get_contacts_by_lead(lead_id: int, subdomain: str, headers: dict):
    """Получение контактов сделки по id сделки"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads/{lead_id}?with=contacts"

    async with client_session.get(url, headers=headers) as response:

        if response.status == 200:
            data = await response.json()
            contact = [contact["id"] for contact in data["_embedded"]["contacts"]][0]
            print(contact)
            return contact
        else:
            print(f"Ошибка: {response.status}")
            return None


async def get_responsible_user_contact(contact_id: int, headers: dict, subdomain: str):
    """Получение ответственного контакта по id"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/contacts/{contact_id}"

    async with client_session.get(url, headers=headers) as response:
        data = await response.json()
        return data["responsible_user_id"]


async def get_all_contacts(subdomain: str, headers: dict):
    """Получение всех контактов"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/contacts"

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
            print(f"Ошибка: {response.status}")
            return []


async def get_company_lead(lead_id: int, subdomain: str, headers: dict):
    """Получение компаний сделки по id сделки"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads/{lead_id}?with=companies"

    async with client_session.get(url, headers=headers) as response:

        if response.status == 200:
            data = await response.json()
            company_id = next(iter(data["_embedded"]["companies"]), {}).get("id", None)
            return company_id
        else:
            print(f"Ошибка: {response.status}")
            return None


async def get_lead_by_id(lead_id: int, subdomain: str, headers: dict):
    """Получение объекта сделки по id сделки"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/leads/{lead_id}"

    async with client_session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            return data
        else:
            print(f"Ошибка: {response.status}")
            return None


async def get_responsible_user_company(company_id: int, subdomain: str, headers: dict):
    """Получение ответственного компании по id"""

    url = f"https://{subdomain}.amocrm.ru/api/v4/companies/{company_id}"

    async with client_session.get(url, headers=headers) as response:
        data = await response.json()
        return data["responsible_user_id"]


async def get_all_companies():
    """Получение всех компаний"""

    url = f"https://{SUBDOMAIN}.amocrm.ru/api/v4/companies"

    async with client_session.get(url, headers=HEADERS) as response:

        if response.status == 200:
            data = await response.json()
            companies = []
            # Формируем список словарей содержащих id компании и его ответственного
            for company in data["_embedded"]["companies"]:
                companies.append(
                    {
                        "id": company["id"],
                        "responsible_user_id": company["responsible_user_id"],
                    }
                )
            return companies
        else:
            print(f"Ошибка: {response.status}")
            return []
