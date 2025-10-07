from sqlalchemy.orm import DeclarativeBase


class BaseORMModel(DeclarativeBase):
    __enabled__ = True
