import logging

from openg2p_bg_task_models.errors import BGTaskException
from openg2p_bg_task_models.models import BeneficiaryListSummary
from openg2p_bg_task_models.schemas import (
    SummaryRequest,
    SummaryResponse,
)
from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..services import SummaryService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class SummaryController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["PBMS Background Task Summary"]
        self.summary_service = SummaryService.get_component()

        self.router.add_api_route(
            "/summary",
            self.get_summary,
            responses={200: {"model": SummaryResponse}},
            methods=["POST"],
        )

    async def get_summary(self, summary_request: SummaryRequest) -> SummaryResponse:
        _logger.debug("Beneficiary List Summary Request: %s", summary_request)

        try:
            beneficiary_list_summary: BeneficiaryListSummary = (
                await self.summary_service.get_summary(summary_request.message)
            )
            summary_response: SummaryResponse = (
                await self.summary_service.construct_summary_success_response(
                    summary_request, beneficiary_list_summary
                )
            )
            _logger.info("Eligibility summary retrieved successfully")
            _logger.debug("Summary Response: %s", summary_response)
            return summary_response

        except BGTaskException as e:
            error_response: SummaryResponse = (
                await self.summary_service.construct_summary_error_response(
                    summary_request, e.code
                )
            )
            return error_response
