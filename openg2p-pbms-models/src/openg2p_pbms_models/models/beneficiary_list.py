from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PBeneficiaryList(BaseORMModel):
    __tablename__ = "g2p_beneficiary_list"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id = mapped_column(
        Integer, ForeignKey("g2p_program_definition.id"), nullable=False
    )
    enrollment_cycle_id = mapped_column(
        Integer, ForeignKey("g2p_enrollment_cycle.id"), nullable=True
    )
    disbursement_cycle_id = mapped_column(
        Integer, ForeignKey("g2p_disbursement_cycle.id"), nullable=True
    )
    eligibility_number_of_attempts = mapped_column(Integer, nullable=True)
    entitlement_number_of_attempts = mapped_column(Integer, nullable=True)
    envelope_creation_number_of_attempts = mapped_column(Integer, nullable=True)
    dbc_number_of_attempts = mapped_column(Integer, nullable=True)
    number_of_registrants = mapped_column(Integer, nullable=True)
    number_of_entitlements_processed = mapped_column(Integer, nullable=True)
    create_uid = mapped_column(Integer, nullable=True)
    write_uid = mapped_column(Integer, nullable=True)
    beneficiary_list_id = mapped_column(String, index=True, unique=True, nullable=False)
    mnemonic = mapped_column(String, nullable=False)
    eligibility_process_status = mapped_column(String, nullable=True)
    eligibility_latest_error_code = mapped_column(String, nullable=True)
    entitlement_process_status = mapped_column(String, nullable=True)
    entitlement_latest_error_code = mapped_column(String, nullable=True)
    envelope_creation_status = mapped_column(String, nullable=True)
    envelope_creation_latest_error_code = mapped_column(String, nullable=True)
    disbursement_batch_creation_status = mapped_column(String, nullable=True)
    dbc_latest_error_code = mapped_column(String, nullable=True)
    list_stage = mapped_column(String, nullable=True)
    list_workflow_status = mapped_column(String, nullable=True)
    approval_date = mapped_column(Date, nullable=True)  # Using DateTime for date
    brief = mapped_column(Text, nullable=True)
    eligibility_processed_date = mapped_column(DateTime, nullable=True)
    entitlement_processed_date = mapped_column(DateTime, nullable=True)
    envelope_creation_processed_date = mapped_column(DateTime, nullable=True)
    dbc_processed_date = mapped_column(DateTime, nullable=True)
    creation_date = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_date = mapped_column(DateTime, nullable=True)
    create_date = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    write_date = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
