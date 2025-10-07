from datetime import date
from typing import List, Optional

from openg2p_fastapi_common.schemas import (
    G2PPaginationRequest,
    G2PRequest,
    G2PRequestBody,
    G2PRequestHeader,
    G2PResponse,
    G2PResponseBody,
)
from pydantic import BaseModel


class BenefitCode(BaseModel):
    id: int
    benefit_code_mnemonic: str
    benefit_type: str
    benefit_code_description: str
    benefit_code_max_quantity: float
    measurement_unit: str


class BenefitProgram(BaseModel):
    id: int
    program_name: str
    program_mnemonic: str
    program_description: str
    am_i_enrolled: bool
    enrolment_date: Optional[date] = None
    benefit_codes: List[BenefitCode]


class BenefitProgramRequestPayload(BaseModel):
    # Only needed for get_program; others can omit payload
    program_id: str | None = None
    application_url: str | None = None


class BenefitProgramRequestBody(G2PRequestBody):
    pagination_request: G2PPaginationRequest | None = None
    request_payload: BenefitProgramRequestPayload | None = None


class BenefitProgramRequest(G2PRequest):
    request_header: G2PRequestHeader
    request_body: BenefitProgramRequestBody


class BenefitProgramResponseBody(G2PResponseBody):
    response_payload: List[BenefitProgram]


class BenefitProgramDetailResponseBody(G2PResponseBody):
    response_payload: Optional[BenefitProgram] = None


class BenefitProgramResponse(G2PResponse):
    response_body: BenefitProgramResponseBody


class BenefitProgramDetailResponse(G2PResponse):
    response_body: BenefitProgramDetailResponseBody
