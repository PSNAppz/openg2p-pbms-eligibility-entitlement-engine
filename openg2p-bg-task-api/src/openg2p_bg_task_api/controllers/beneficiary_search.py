import logging

from openg2p_bg_task_models.errors import BGTaskException
from openg2p_bg_task_models.schemas import (
    BeneficiarySearchRequest,
    BeneficiarySearchResponse,
    BeneficiarySearchResponsePayload,
)
from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..services import BeneficiarySearchService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class BeneficiarySearchController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["PBMS Background Task Beneficiary Search"]
        self.beneficiary_search_service = BeneficiarySearchService.get_component()

        self.router.add_api_route(
            "/search_beneficiaries",
            self.search_beneficiaries,
            responses={200: {"model": BeneficiarySearchResponse}},
            methods=["POST"],
        )

    async def search_beneficiaries(
        self, beneficiary_search_request: BeneficiarySearchRequest
    ) -> BeneficiarySearchResponse:
        _logger.debug("Beneficiary Search Request: %s", beneficiary_search_request)

        try:
            beneficiary_search_response_payload: BeneficiarySearchResponsePayload = (
                await self.beneficiary_search_service.search_beneficiaries(
                    beneficiary_search_request.message
                )
            )
            beneficiary_search_response: BeneficiarySearchResponse = await self.beneficiary_search_service.construct_beneficiary_search_success_response(
                beneficiary_search_request, beneficiary_search_response_payload
            )
            _logger.info("Beneficiaries retrieved successfully")
            _logger.debug(
                "Beneficiary Search Response: %s", beneficiary_search_response
            )
            return beneficiary_search_response

        except BGTaskException as e:
            error_response: BeneficiarySearchResponse = await self.beneficiary_search_service.construct_beneficiary_search_error_response(
                beneficiary_search_request, e.code
            )
            return error_response
