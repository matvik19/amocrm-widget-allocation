from typing import List, Optional, Dict

from pydantic import BaseModel


class UpdateManagers(BaseModel):
    managers: Dict[int, bool]


class CreateManagers(UpdateManagers):
    subdomain: str
