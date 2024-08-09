from sqlalchemy import Column, Integer, Boolean, BigInteger, String
from src.database import Base


class ManagerStatus(Base):
    __tablename__ = "manager_status"

    manager_id = Column(BigInteger, primary_key=True)
    subdomain = Column(String, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
