import uuid
from datetime import datetime, timezone

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import mapped_column


class BeneficiaryListSummary(BaseORMModel):
    __abstract__ = True

    id = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )
    program_id = mapped_column(Integer, nullable=False)
    program_mnemonic = mapped_column(String, nullable=False)
    target_registry = mapped_column(String, nullable=False)
    beneficiary_list_id = mapped_column(String, index=True, unique=True, nullable=False)
    number_of_registrants = mapped_column(Integer, nullable=False)
    number_of_entitlements_processed = mapped_column(Integer, nullable=False, default=0)

    total_disbursement_quantity = mapped_column(JSON, nullable=True)
    average_entitlement_per_person = mapped_column(JSON, nullable=True)
    entitlement_amount_q1 = mapped_column(JSON, nullable=True)
    entitlement_amount_q2 = mapped_column(JSON, nullable=True)
    entitlement_amount_q3 = mapped_column(JSON, nullable=True)

    date_created = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
