from enum import Enum

from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class G2PRegistry(BaseORMModel):
    __abstract__ = True

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_registry_id = mapped_column(String, nullable=True)
