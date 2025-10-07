from sqlalchemy import TIMESTAMP, Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from .base import BaseORMModel


class G2PEnrollmentCycle(BaseORMModel):
    __tablename__ = "g2p_enrollment_cycle"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_number = mapped_column(Integer, nullable=False)
    program_id = mapped_column(
        Integer, ForeignKey("g2p_program_definition.id"), nullable=False
    )
    create_uid = mapped_column(Integer, nullable=True)
    write_uid = mapped_column(Integer, nullable=True)
    enrollment_cycle_id = mapped_column(String, nullable=True)
    enrollment_start_date = mapped_column(Date, nullable=False)
    enrollment_end_date = mapped_column(Date, nullable=False)
    disbursement_start_date = mapped_column(Date, nullable=False)
    disbursement_end_date = mapped_column(Date, nullable=False)
    approved_for_enrollment = mapped_column(Boolean, nullable=True)
    create_date = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    write_date = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    beneficiary_list_ids = relationship(
        "G2PBeneficiaryList", backref="enrollment_cycle"
    )
