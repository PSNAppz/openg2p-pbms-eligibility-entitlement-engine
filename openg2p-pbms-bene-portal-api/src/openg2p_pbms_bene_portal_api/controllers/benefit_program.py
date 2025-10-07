import logging
from typing import Annotated

from fastapi import Depends
from openg2p_fastapi_auth.beneficiary_token import BeneficiaryToken
from openg2p_fastapi_auth.models.credentials import AuthCredentials
from openg2p_fastapi_common.controller import BaseController
from openg2p_pbms_models.errors import PBMSException
from openg2p_pbms_models.schemas import (
    BenefitProgramDetailResponse,
    BenefitProgramRequest,
    BenefitProgramResponse,
)

from ..config import Settings
from ..services import BenefitProgramService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class BenefitProgramController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["PBMS Bene Portal - Benefit Programs"]
        self.benefit_programs_service = BenefitProgramService.get_component()
        self.router.prefix = "/benefit_program"

        self.router.add_api_route(
            "/get_my_programs",
            self.get_my_programs,
            responses={200: {"model": BenefitProgramResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_all_programs",
            self.get_all_programs,
            responses={200: {"model": BenefitProgramResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_program",
            self.get_program,
            responses={200: {"model": BenefitProgramDetailResponse}},
            methods=["POST"],
        )

    async def get_my_programs(
        self,
        benefit_program_request: BenefitProgramRequest,
        auth_credentials: Annotated[AuthCredentials, Depends(BeneficiaryToken())],
    ) -> BenefitProgramResponse:
        _logger.debug("Get My Programs Request: %s", benefit_program_request)
        try:
            _logger.info("Authenticated Beneficiary ID: %s", auth_credentials)
            if not auth_credentials:
                _logger.error("Authentication credentials are missing")
                raise PBMSException(
                    code="AUTH001", message="Authentication credentials are missing"
                )
            beneficiary_id = auth_credentials.preferred_username
            _logger.info("Fetching programs for Beneficiary ID: %s", beneficiary_id)
            benefit_programs_response: BenefitProgramResponse = (
                await self.benefit_programs_service.get_my_programs(
                    beneficiary_id, benefit_program_request
                )
            )
            _logger.info("Benefit programs retrieved successfully")
            _logger.debug("Get My Programs Response: %s", benefit_programs_response)
            return benefit_programs_response
        except PBMSException as e:
            error_response: BenefitProgramResponse = await self.benefit_programs_service.construct_benefit_program_failure_response(
                benefit_program_request, e.code, e.message
            )
            return error_response

    async def get_all_programs(
        self,
        benefit_program_request: BenefitProgramRequest,
        auth_credentials: Annotated[AuthCredentials, Depends(BeneficiaryToken())],
    ) -> BenefitProgramResponse:
        _logger.debug("Get All Programs Request: %s", benefit_program_request)
        try:
            _logger.info("Authenticated Beneficiary ID: %s", auth_credentials)
            if not auth_credentials:
                _logger.error("Authentication credentials are missing")
                raise PBMSException(
                    code="AUTH001", message="Authentication credentials are missing"
                )
            beneficiary_id = auth_credentials.preferred_username
            _logger.info("Fetching all programs for Beneficiary ID: %s", beneficiary_id)
            benefit_programs_response: BenefitProgramResponse = (
                await self.benefit_programs_service.get_all_programs(
                    beneficiary_id, benefit_program_request
                )
            )
            _logger.info("All programs retrieved successfully")
            _logger.debug("Get All Programs Response: %s", benefit_programs_response)
            return benefit_programs_response
        except PBMSException as e:
            error_response: BenefitProgramResponse = await self.benefit_programs_service.construct_benefit_program_failure_response(
                benefit_program_request, e.code, e.message
            )
            return error_response

    async def get_program(
        self,
        benefit_program_request: BenefitProgramRequest,
        auth_credentials: Annotated[AuthCredentials, Depends(BeneficiaryToken())],
    ) -> BenefitProgramDetailResponse:
        _logger.debug("Get Program Request: %s", benefit_program_request)
        try:
            _logger.info("Authenticated Beneficiary ID: %s", auth_credentials)
            if not auth_credentials:
                _logger.error("Authentication credentials are missing")
                raise PBMSException(
                    code="AUTH001", message="Authentication credentials are missing"
                )
            beneficiary_id = auth_credentials.preferred_username
            _logger.info(
                "Fetching program detail for Beneficiary ID: %s", beneficiary_id
            )
            program_response: BenefitProgramDetailResponse = (
                await self.benefit_programs_service.get_program(
                    beneficiary_id, benefit_program_request
                )
            )
            _logger.info("Program retrieved successfully")
            _logger.debug("Get Program Response: %s", program_response)
            return program_response
        except PBMSException as e:
            error_response: BenefitProgramDetailResponse = await self.benefit_programs_service.construct_benefit_program_detail_failure_response(
                benefit_program_request, e.code, e.message
            )
            return error_response
