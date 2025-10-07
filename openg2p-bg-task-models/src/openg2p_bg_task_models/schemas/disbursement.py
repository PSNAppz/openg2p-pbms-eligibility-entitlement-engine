from pydantic import BaseModel


class Disbursement(BaseModel):
    beneficiary_id: str
    disbursement_id: str
    entitlement: float
    compute_elements: dict
