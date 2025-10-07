from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class ProgramStatus(Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


class DisbursementFrequency(Enum):
    Daily = "Daily"
    Weekly = "Weekly"
    Fortnightly = "Fortnightly"
    Monthly = "Monthly"
    BiMonthly = "BiMonthly"
    Quarterly = "Quarterly"
    SemiAnnually = "SemiAnnually"
    Annually = "Annually"
    OnDemand = "OnDemand"


class BeneficiaryList(Enum):
    latest_always = "latest_always"
    labeled = "labeled"


class G2PProgramDefinition(BaseORMModel):
    __tablename__ = "g2p_program_definition"

    id = mapped_column(Integer, primary_key=True)
    program_mnemonic = mapped_column(String, nullable=False)
    description = mapped_column(String)

    target_registry = mapped_column(String, nullable=False)
    program_status = mapped_column(SqlEnum(ProgramStatus), nullable=False)
    disbursement_frequency = mapped_column(
        SqlEnum(DisbursementFrequency), nullable=True
    )
    enrollment_frequency = mapped_column(SqlEnum(DisbursementFrequency), nullable=True)
    beneficiary_list = mapped_column(SqlEnum(BeneficiaryList), nullable=False)

    service_providers_required = mapped_column(Boolean, default=True)
    on_demand_cycle_allowed = mapped_column(Boolean, default=False)

    # Many2many placeholder (actual association table/model needed for full support)
    # benefit_code_ids = relationship("G2PBenefitCodes", secondary="program_benefit_codes", back_populates="programs")

    # One2many/relationship placeholders (actual models/foreign keys needed for full support)
    # beneficiary_list_ids = mapped_column(JSON, nullable=True)
    # enrollment_cycle_ids = mapped_column(JSON, nullable=True)
    # disbursement_cycle_ids = mapped_column(JSON, nullable=True)
    # eligibility_rule_ids = mapped_column(JSON, nullable=True)
    # entitlement_rule_ids = mapped_column(JSON, nullable=True)

    show_label_for_beneficiary_list = mapped_column(Boolean, default=False)
    verifications_for_enrolment = mapped_column(Integer, nullable=True)
    verifications_for_disbursement = mapped_column(Integer, nullable=True)

    label_for_beneficiary_list_id = mapped_column(
        Integer, ForeignKey("g2p_beneficiary_list.id"), nullable=True
    )

    create_uid = mapped_column(Integer)
    write_uid = mapped_column(Integer)
    create_date = mapped_column(DateTime)
    write_date = mapped_column(DateTime)
