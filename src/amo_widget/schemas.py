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


class AllocationAllByCompanyContacts(BaseModel):
    pipeline_id: int
    status_id: int
    update_tasks: bool
    subdomain: str


class AllocationNewLeadByCompany(BaseModel):
    lead_id: int
    update_tasks: bool
    subdomain: str


class ConfigWidgetBody(BaseModel):
    """Тело запроса, который отправляется при настройке виджета"""

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


class TriggerBody(BaseModel):
    """Тело запроса, который отправляется триггером"""

    lead_id: int
    users_ids: List[int]
    status: int
    necessary_quantity_leads: List[int]
