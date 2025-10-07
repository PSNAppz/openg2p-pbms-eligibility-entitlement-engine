import logging
from datetime import datetime
from typing import List

from openg2p_bg_task_models.errors import BGTaskErrorCodes, BGTaskException
from openg2p_bg_task_models.models import DisbursementBatch, DisbursementEnvelope
from openg2p_bg_task_models.schemas import (
    DisbursementBatchRequest,
    DisbursementBatchRequestPayload,
    DisbursementBatchResponse,
    DisbursementBatchResponsePayload,
    DisbursementEnvelopeRequest,
    DisbursementEnvelopeRequestPayload,
    DisbursementEnvelopeResponse,
    DisbursementEnvelopeResponsePayload,
)
from openg2p_fastapi_common.service import BaseService
from openg2p_g2pconnect_common_lib.schemas import (
    StatusEnum,
    SyncResponseHeader,
)
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings
from ..engine import get_engine

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


class DisbursementEnvelopeService(BaseService):
    async def disbursement_envelope(
        self, disbursement_envelope_request_payload: DisbursementEnvelopeRequestPayload
    ) -> DisbursementEnvelopeResponsePayload:
        session_maker = async_sessionmaker(
            bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
        )
        async with session_maker() as session:
            try:
                _logger.info(
                    f"Fetching disbursement envelopes for beneficiary list id: {disbursement_envelope_request_payload.beneficiary_list_id}"
                )
                disbursement_envelopes = await session.execute(
                    DisbursementEnvelope.__table__.select().where(
                        DisbursementEnvelope.beneficiary_list_id
                        == disbursement_envelope_request_payload.beneficiary_list_id
                    )
                )
                disbursement_envelopes = disbursement_envelopes.fetchall()
                disbursement_envelopes: List[dict] = [
                    dict(row._mapping) for row in disbursement_envelopes
                ]
                _logger.debug(
                    f"Disbursement envelopes fetched: {disbursement_envelopes}"
                )

                return DisbursementEnvelopeResponsePayload(
                    beneficiary_list_id=disbursement_envelope_request_payload.beneficiary_list_id,
                    disbursement_envelopes=disbursement_envelopes,
                )

            except Exception as e:
                _logger.error(f"Error fetching disbursement envelopes : {e}")
                raise BGTaskException(
                    message="Disbursement Envelope Request Invalid",
                    code=BGTaskErrorCodes.INVALID_REQUEST,
                ) from e

    async def construct_disbursement_envelope_success_response(
        self,
        disbursement_envelope_request: DisbursementEnvelopeRequest,
        disbursement_envelope_response_payload: DisbursementEnvelopeResponsePayload,
    ) -> DisbursementEnvelopeResponse:
        disbursement_envelope_response = DisbursementEnvelopeResponse(
            header=SyncResponseHeader(
                message_id=disbursement_envelope_request.header.message_id,
                message_ts=datetime.now().isoformat(),
                action=disbursement_envelope_request.header.action,
                status=StatusEnum.succ,
            ),
            message=disbursement_envelope_response_payload,
        )
        return disbursement_envelope_response

    async def construct_disbursement_envelope_error_response(
        self,
        disbursement_envelope_request: DisbursementEnvelopeRequest,
        error_code: str,
    ) -> DisbursementEnvelopeResponse:
        disbursement_envelope_response = DisbursementEnvelopeResponse(
            header=SyncResponseHeader(
                message_id=disbursement_envelope_request.header.message_id,
                message_ts=datetime.now().isoformat(),
                action=disbursement_envelope_request.header.action,
                status=StatusEnum.rjct,
                status_reason_message=error_code,
            ),
            message={},
        )
        return disbursement_envelope_response


class DisbursementBatchService(BaseService):
    async def disbursement_batch(
        self, disbursement_batch_request_payload: DisbursementBatchRequestPayload
    ) -> DisbursementBatchResponsePayload:
        session_maker = async_sessionmaker(
            bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
        )
        async with session_maker() as session:
            try:
                _logger.info(
                    f"Fetching disbursement batches for beneficiary list id: {disbursement_batch_request_payload.beneficiary_list_id}"
                )
                disbursement_batches = await session.execute(
                    DisbursementBatch.__table__.select().where(
                        DisbursementBatch.beneficiary_list_id
                        == disbursement_batch_request_payload.beneficiary_list_id
                    )
                )
                disbursement_batches = disbursement_batches.fetchall()
                disbursement_batches: List[dict] = [
                    dict(row._mapping) for row in disbursement_batches
                ]
                _logger.debug(f"Disbursement batches fetched: {disbursement_batches}")

                return DisbursementBatchResponsePayload(
                    beneficiary_list_id=disbursement_batch_request_payload.beneficiary_list_id,
                    disbursement_batches=disbursement_batches,
                )

            except Exception as e:
                _logger.error(f"Error fetching disbursement batches : {e}")
                raise BGTaskException(
                    message="Disbursement Batch Request Invalid",
                    code=BGTaskErrorCodes.INVALID_REQUEST,
                ) from e

    async def construct_disbursement_batch_success_response(
        self,
        disbursement_batch_request: DisbursementBatchRequest,
        disbursement_batch_response_payload: DisbursementBatchResponsePayload,
    ) -> DisbursementBatchResponse:
        disbursement_batch_response = DisbursementBatchResponse(
            header=SyncResponseHeader(
                message_id=disbursement_batch_request.header.message_id,
                message_ts=datetime.now().isoformat(),
                action=disbursement_batch_request.header.action,
                status=StatusEnum.succ,
            ),
            message=disbursement_batch_response_payload,
        )
        return disbursement_batch_response

    async def construct_disbursement_batch_error_response(
        self, disbursement_batch_request: DisbursementBatchRequest, error_code: str
    ) -> DisbursementBatchResponse:
        disbursement_batch_response = DisbursementBatchResponse(
            header=SyncResponseHeader(
                message_id=disbursement_batch_request.header.message_id,
                message_ts=datetime.now().isoformat(),
                action=disbursement_batch_request.header.action,
                status=StatusEnum.rjct,
                status_reason_message=error_code,
            ),
            message={},
        )
        return disbursement_batch_response
