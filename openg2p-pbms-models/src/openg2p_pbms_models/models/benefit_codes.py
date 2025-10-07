from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PBenefitCodes(BaseORMModel):
    __tablename__ = "g2p_benefit_codes"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    decimal_places = mapped_column(Integer, nullable=True)
    create_uid = mapped_column(Integer, nullable=True)
    write_uid = mapped_column(Integer, nullable=True)
    benefit_mnemonic = mapped_column(String, unique=True, nullable=False)
    benefit_type = mapped_column(String, nullable=False)
    decimal_places = mapped_column(Integer, nullable=True)
    measurement_unit = mapped_column(String, nullable=True)
    benefit_description = mapped_column(Text, nullable=True)
    create_date = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    write_date = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
