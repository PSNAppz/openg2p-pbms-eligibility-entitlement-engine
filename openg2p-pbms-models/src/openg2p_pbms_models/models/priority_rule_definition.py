from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PPriorityRuleDefinition(BaseORMModel):
    __tablename__ = "g2p_priority_rule_definition"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    mnemonic = mapped_column(String, nullable=False)
    description = mapped_column(String, nullable=True)
    disbursement_cycle_id = mapped_column(
        Integer, ForeignKey("g2p_disbursement_cycle.id"), nullable=True
    )
    program_id = mapped_column(Integer, nullable=True)
    target_registry = mapped_column(String, nullable=False)
    pbms_domain = mapped_column(String, nullable=False)
    sql_query = mapped_column(String, nullable=False)
