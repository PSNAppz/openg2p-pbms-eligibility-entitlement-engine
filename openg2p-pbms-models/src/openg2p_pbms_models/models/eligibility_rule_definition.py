from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PEligibilityRuleDefinition(BaseORMModel):
    __tablename__ = "g2p_eligibility_rule_definition"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id = mapped_column(
        Integer, ForeignKey("g2p_program_definition.id"), nullable=False
    )
    create_uid = mapped_column(Integer, nullable=True)
    write_uid = mapped_column(Integer, nullable=True)
    mnemonic = mapped_column(String, nullable=False, unique=True)
    rule_number = mapped_column(Integer, nullable=False)
    set_operator = mapped_column(String, nullable=True)
    description = mapped_column(String, nullable=True)
    target_registry = mapped_column(String, nullable=False)
    pbms_domain = mapped_column(String, nullable=False)
    sql_query = mapped_column(String, nullable=True)
    create_date = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    write_date = mapped_column(TIMESTAMP(timezone=False), nullable=True)
