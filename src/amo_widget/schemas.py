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
    users_ids: List[int]
    percents: List[int]
    statuses_ids: List[int]
    max_counts: List[int] | None
    ignore_manager: int
    status_id: int
    pipeline_id: int
    lead_id: int


class TriggerBody(BaseModel):
    """Тело запроса, который отправляется триггером"""

    lead_id: int
    users_ids: List[int]
    status: int
    necessary_quantity_leads: List[int]


class TestBody(BaseModel):
    client_id: str
    subdomain: str

    # Учитывающиеся факторы
    use_contact: bool
    use_company: bool

    # Дополнительный функционал
    update_tasks: bool
    accept_to_existing_leads: bool

    # Данные для распределения
    users_ids: List[int]
    percents: List[int]
    lead_id: int
    max_counts: List[int] | None
