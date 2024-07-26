from typing import List, Optional, Dict

from pydantic import BaseModel


class AllocationAllByPercentBody(BaseModel):
    pipeline_id: int
    users_ids: List[int]
    percents: List[int]
    status_id: int
    update_tasks: bool
    subdomain: str


class AllocationAllByMaxCountBody(BaseModel):
    pipeline_id: int
    users_ids: List[int]
    necessary_quantity_leads: List[int]
    status_id: int
    update_tasks: bool
    subdomain: str


class AllocationNewLeadByPercentBody(BaseModel):
    lead_id: int
    pipeline_id: int
    users_ids: List[int]
    percents: List[int]
    status_id: int
    update_tasks: bool


class AllocationNewLeadByMaxCountBody(BaseModel):
    lead_id: int
    pipeline_id: int
    users_ids: List[int]
    status_id: int
    necessary_quantity_leads: List[int]


class AllocationNewLeadByCompanyContacts(BaseModel):
    lead_id: int
    update_tasks: bool
    subdomain: str
    ignore_manager: int


class ConfigWidgetBody(BaseModel):
    """Тело запроса, который отправляется при настройке виджета"""

    client_id: str
    subdomain: str

    # Дополнительный функционал
    update_tasks: bool
    update_contacts: bool
    update_companies: bool
    accept_to_existing_leads: bool

    # Данные для распределения
    schedule: List[int]
    users_ids: List[int]
    percents: List[int]
    statuses_ids: List[int]
    max_counts: List[int] | None
    ignore_manager: int
    status_id: int
    pipeline_id: int
    lead_id: int


class ConfigResponse(BaseModel):
    status: str
    lead_id: int
    massage: str
