from datetime import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP
from src.database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    client_id = Column(String, nullable=False)
    subdomain = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    date_of_refresh = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)