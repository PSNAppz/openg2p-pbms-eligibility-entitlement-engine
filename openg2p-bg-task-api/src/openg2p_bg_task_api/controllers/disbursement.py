import logging

from openg2p_bg_task_models.errors import BGTaskException
from openg2p_bg_task_models.schemas import (
    DisbursementBatchRequest,
    DisbursementBatchResponse,
    DisbursementBatchResponsePayload,
    DisbursementEnvelopeRequest,
    DisbursementEnvelopeResponse,
    DisbursementEnvelopeResponsePayload,
)
from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..services import DisbursementBatchService, DisbursementEnvelopeService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class DisbursementController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["PBMS Background Task Disbursement"]

        self.disbursement_envelope_service = DisbursementEnvelopeService.get_component()
        self.disbursement_batch_service = DisbursementBatchService.get_component()

        self.router.add_api_route(
            "/disbursement_envelope",
            self.disbursement_envelope,
            responses={200: {"model": DisbursementEnvelopeResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/disbursement_batch",
            self.disbursement_batch,
            responses={200: {"model": DisbursementBatchResponse}},
            methods=["POST"],
        )

    async def disbursement_envelope(
        self, disbursement_envelope_request: DisbursementEnvelopeRequest
    ) -> DisbursementEnvelopeResponse:
        _logger.debug(
            "Disbursement Envelope Request: %s", disbursement_envelope_request
        )

        try:
            disbursement_envelope_response_payload: DisbursementEnvelopeResponsePayload = await self.disbursement_envelope_service.disbursement_envelope(
                disbursement_envelope_request.message
            )
            disbursement_envelope_response: DisbursementEnvelopeResponse = await self.disbursement_envelope_service.construct_disbursement_envelope_success_response(
                disbursement_envelope_request, disbursement_envelope_response_payload
            )
            _logger.info("Disbursement Envelopes retrived successfully")
            _logger.debug(
                "Disbursement Envelope response: %s", disbursement_envelope_response
            )
            return disbursement_envelope_response

        except BGTaskException as e:
            error_response: DisbursementEnvelopeResponse = await self.disbursement_envelope_service.construct_disbursement_envelope_error_response(
                disbursement_envelope_request, e.code
            )
            return error_response

    async def disbursement_batch(
        self, disbursement_batch_request: DisbursementBatchRequest
    ) -> DisbursementBatchResponse:
        _logger.debug("Disbursement Batch Request: %s", disbursement_batch_request)

        try:
            disbursement_batch_response_payload: DisbursementBatchResponsePayload = (
                await self.disbursement_batch_service.disbursement_batch(
                    disbursement_batch_request.message
                )
            )
            disbursement_batch_response: DisbursementBatchResponse = await self.disbursement_batch_service.construct_disbursement_batch_success_response(
                disbursement_batch_request, disbursement_batch_response_payload
            )
            _logger.info("Disbursement Batches retrived successfully")
            _logger.debug(
                "Disbursement Batch response: %s", disbursement_batch_response
            )
            return disbursement_batch_response

        except BGTaskException as e:
            error_response: DisbursementBatchResponse = await self.disbursement_batch_service.construct_disbursement_batch_error_response(
                disbursement_batch_request, e.code
            )
            return error_response
