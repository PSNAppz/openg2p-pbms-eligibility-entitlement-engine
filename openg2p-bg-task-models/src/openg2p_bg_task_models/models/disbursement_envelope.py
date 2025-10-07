import enum

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import mapped_column


class BenefitType(enum.Enum):
    COMMODITY = "COMMODITY"
    SERVICE = "SERVICE"
    CASH_DIGITAL = "CASH_DIGITAL"
    CASH_PHYSICAL = "CASH_PHYSICAL"
    COMBINATION = "COMBINATION"


class DisbursementEnvelope(BaseORMModel):
    __tablename__ = "disbursement_envelope"
    __table_args__ = (
        UniqueConstraint(
            "beneficiary_list_id",
            "benefit_code_id",
            name="uq_beneficiary_list_id_benefit_code_id",
        ),
    )

    id = mapped_column(String, primary_key=True, nullable=False)
    beneficiary_list_id = mapped_column(String, nullable=False, index=True)
    benefit_code_id = mapped_column(Integer, nullable=False, index=True)
    benefit_type = mapped_column(SqlEnum(BenefitType), nullable=False)
    benefit_program_id = mapped_column(Integer, nullable=False, index=True)
    benefit_program_mnemonic = mapped_column(String, nullable=False)
    disbursement_cycle_id = mapped_column(Integer, nullable=False)
    cycle_code_mnemonic = mapped_column(String, nullable=False)
    number_of_beneficiaries = mapped_column(Integer, nullable=False)
    number_of_disbursements = mapped_column(Integer, nullable=False)
    total_disbursement_quantity = mapped_column(Float, nullable=False)
    measurement_unit = mapped_column(String, nullable=False)
    disbursement_schedule_date = mapped_column(DateTime, nullable=False)
