import uuid

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import mapped_column

from .status_enum import StatusEnum


class DisbursementBatch(BaseORMModel):
    __tablename__ = "disbursement_batch"

    id = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )
    beneficiary_list_id = mapped_column(String, nullable=False)
    disbursement_cycle_id = mapped_column(String, nullable=False)
    beneficiary_list_details_id = mapped_column(String, nullable=False)
    disbursement_envelope_id = mapped_column(String, nullable=False)
    disbursements = mapped_column(JSON, nullable=False)
    benefit_code_id = mapped_column(Integer, nullable=False)
    measurement_unit = mapped_column(String, nullable=False)
    number_of_beneficiaries = mapped_column(Integer, nullable=False)
    number_of_disbursements = mapped_column(Integer, nullable=False)
    total_disbursement_quantity = mapped_column(Float, nullable=False)
    disbursement_status = mapped_column(
        String, nullable=False, default=StatusEnum.pending.value
    )
    disbursement_number_of_attempts = mapped_column(Integer, nullable=True, default=0)
    disbursement_latest_error_code = mapped_column(String, nullable=True, default=None)
    disbursement_processed_date = mapped_column(DateTime, nullable=True, default=None)
