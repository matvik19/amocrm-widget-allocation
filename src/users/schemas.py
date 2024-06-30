from pydantic import BaseModel


class UserCreate(BaseModel):
    client_id: str
    subdomain: str
    access_token: str
    refresh_token: str
