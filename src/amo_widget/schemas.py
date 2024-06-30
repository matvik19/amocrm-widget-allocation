from typing import List

from pydantic import BaseModel


class AllocationAllByPercentBody(BaseModel):
    pipeline_id: int
    users_ids: List[int]
    percents: List[int]
    status: int
    update_tasks: bool


class AllocationAllByMaxCountBody(BaseModel):
    pipeline_id: int
    users_ids: List[int]
    necessary_quantity_leads: List[int]
    status: int
    update_tasks: bool


class AllocationNewLeadByPercentBody(BaseModel):
    lead_id: int
    pipeline_id: int
    users_ids: List[int]
    percents: List[int]
    status: int
    update_tasks: bool


class AllocationNewLeadByMaxCountBody(BaseModel):
    lead_id: int
    pipeline_id: int
    users_ids: List[int]
    status: int
    necessary_quantity_leads: List[int]


class ConfigWidgetBody(BaseModel):
    """Тело запроса, который отправляется при настройке виджета"""

    # Режим распределения
    mode: str  # percent - по процентам | # max_count - максимальное число

    # Учитывающиеся факторы
    use_contact: bool
    use_company: bool

    # Дополнительный функционал
    update_tasks: bool
    accept_to_existing_leads: bool

    # Данные для распределения
    pipeline_id: int
    users_ids: List[int]
    percents: List[int]
    necessary_quantity_leads: List[int] = []
    status: int


class TriggerBody(BaseModel):
    """Тело запроса, который отправляется триггером"""

    lead_id: int
    users_ids: List[int]
    status: int
    necessary_quantity_leads: List[int]
