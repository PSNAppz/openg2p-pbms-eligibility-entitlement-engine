import logging
from datetime import datetime

from openg2p_bg_task_models.schemas import (
    BeneficiarySearchRequest,
    BeneficiarySearchRequestPayload,
    BeneficiarySearchResponse,
    BeneficiarySearchResponsePayload,
)
from openg2p_bg_task_registry_adapters.factory import RegistryFactory
from openg2p_bg_task_registry_adapters.interface import RegistryInterface
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


class BeneficiarySearchService(BaseService):
    async def search_beneficiaries(
        self, beneficiary_search_request_payload: BeneficiarySearchRequestPayload
    ) -> BeneficiarySearchResponsePayload:
        session_maker = async_sessionmaker(
            bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
        )
        sr_session_maker = async_sessionmaker(
            bind=_engine.get("db_engine_sr"), expire_on_commit=False
        )

        async with session_maker() as session, sr_session_maker() as sr_session:
            try:
                registry_interface: RegistryInterface = (
                    RegistryFactory.get_registry_class(
                        beneficiary_search_request_payload.target_registry
                    )
                )
                beneficiary_search_response_payload: BeneficiarySearchResponsePayload = await registry_interface.search_beneficiaries(
                    session,
                    sr_session,
                    beneficiary_search_request_payload.beneficiary_list_id,
                    beneficiary_search_request_payload.target_registry,
                    beneficiary_search_request_payload.search_query,
                    beneficiary_search_request_payload.page,
                    beneficiary_search_request_payload.page_size,
                    beneficiary_search_request_payload.order_by,
                )
                return beneficiary_search_response_payload

            except Exception as e:
                _logger.exception("Error searching for beneficiaries.")
                raise e

    async def construct_beneficiary_search_success_response(
        self,
        beneficiary_search_request: BeneficiarySearchRequest,
        beneficiary_search_response_payload: BeneficiarySearchResponsePayload,
    ) -> BeneficiarySearchResponse:
        response = BeneficiarySearchResponse(
            header=SyncResponseHeader(
                message_id=beneficiary_search_request.header.message_id,
                message_ts=datetime.now().isoformat(),
                action=beneficiary_search_request.header.action,
                status=StatusEnum.succ,
            ),
            message=beneficiary_search_response_payload,
        )
        return response

    async def construct_beneficiary_search_error_response(
        self,
        beneficiary_search_request: BeneficiarySearchRequest,
        error_code: str,
    ) -> BeneficiarySearchResponse:
        response = BeneficiarySearchResponse(
            header=SyncResponseHeader(
                message_id=beneficiary_search_request.header.message_id,
                message_ts=datetime.now().isoformat(),
                action=beneficiary_search_request.header.action,
                status=StatusEnum.rjct,
                status_reason_message=error_code,
            ),
            message={},
        )

        return response
