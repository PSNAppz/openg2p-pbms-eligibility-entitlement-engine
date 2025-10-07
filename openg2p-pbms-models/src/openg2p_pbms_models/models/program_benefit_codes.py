from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PProgramBenefitCodes(BaseORMModel):
    __tablename__ = "g2p_program_benefit_codes"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id = mapped_column(
        Integer,
        ForeignKey("g2p_program_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
    benefit_code_id = mapped_column(
        Integer, ForeignKey("g2p_benefit_codes.id"), nullable=False
    )
    max_quantity = mapped_column(Float, nullable=False)
