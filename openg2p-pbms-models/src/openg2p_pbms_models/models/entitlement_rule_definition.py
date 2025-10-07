from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PEntitlementRuleDefinition(BaseORMModel):
    __tablename__ = "g2p_entitlement_rule_definition"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id = mapped_column(Integer, nullable=False, index=True)
    benefit_code_id = mapped_column(
        Integer, ForeignKey("g2p_benefit_codes.id"), nullable=True
    )
    target_registry = mapped_column(String, nullable=False)
    create_uid = mapped_column(Integer, nullable=True)
    write_uid = mapped_column(Integer, nullable=True)
    mnemonic = mapped_column(String, nullable=False, unique=True)
    description = mapped_column(String, nullable=True)
    decimal_places = mapped_column(Integer, nullable=True)
    multiplier = mapped_column(String, nullable=True)
    pbms_domain = mapped_column(String, nullable=False)
    sql_query = mapped_column(String, nullable=False)
    create_date = mapped_column(
        String, nullable=True
    )  # Should be DateTime, but using String for "timestamp without time zone"
    write_date = mapped_column(
        String, nullable=True
    )  # Should be DateTime, but using String for "timestamp without time zone"
    quantity = mapped_column(Float, nullable=False)
