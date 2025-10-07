import logging
from datetime import date, datetime
from typing import List

from openg2p_bg_task_models.models.beneficiary_list_details import (
    BeneficiaryListDetails,
)
from openg2p_fastapi_common.schemas import G2PResponseStatus
from openg2p_fastapi_common.service import BaseService
from openg2p_pbms_models.errors import PBMSErrorCodes, PBMSException
from openg2p_pbms_models.models import (
    G2PBeneficiaryList,
    G2PBenefitCodes,
    G2PProgramBenefitCodes,
    G2PProgramDefinition,
)
from openg2p_pbms_models.schemas import (
    BenefitProgram,
    BenefitProgramDetailResponse,
    BenefitProgramDetailResponseBody,
    BenefitProgramRequest,
    BenefitProgramResponse,
    BenefitProgramResponseBody,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings
from ..engine import get_engine

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


class BenefitProgramService(BaseService):
    async def _get_enrollment_status(
        self,
        session_pbms,
        session_bg,
        program_id: int,
        registrant_id: str,
    ) -> tuple[bool, date | None]:
        latest_list_row = (
            await session_pbms.execute(
                select(
                    G2PBeneficiaryList.beneficiary_list_id,
                    G2PBeneficiaryList.approval_date,
                )
                .where(
                    (G2PBeneficiaryList.program_id == program_id)
                    & (G2PBeneficiaryList.approval_date.is_not(None))
                )
                .order_by(G2PBeneficiaryList.approval_date.desc())
                .limit(1)
            )
        ).first()

        if not latest_list_row:
            _logger.info(f"No approved beneficiary list for program_id {program_id}")
            return False, None

        beneficiary_list_id = latest_list_row.beneficiary_list_id
        enrolment_date = latest_list_row.approval_date

        bld = (
            (
                await session_bg.execute(
                    select(BeneficiaryListDetails).where(
                        BeneficiaryListDetails.beneficiary_list_id
                        == beneficiary_list_id
                    )
                )
            )
            .scalars()
            .first()
        )
        if not bld:
            return False, enrolment_date

        registrants = bld.registrant_details or []
        am_i_enrolled = any(
            isinstance(r, dict) and r.get("registrant_id") == registrant_id
            for r in registrants
        )
        return am_i_enrolled, enrolment_date

    async def get_my_programs(
        self, beneficiary_id: str, benefit_program_request: BenefitProgramRequest
    ) -> BenefitProgramResponse:
        _logger.info(
            "Get My Programs Request",
        )
        pagination = (
            benefit_program_request.request_body.pagination_request
            if benefit_program_request.request_body
            else None
        )

        # Extract pagination parameters
        page_size = pagination.page_size if pagination else 10
        current_page = pagination.current_page if pagination else 1
        offset = (current_page - 1) * page_size

        session_maker_pbms = async_sessionmaker(
            bind=_engine.get("db_engine_pbms"), expire_on_commit=False
        )
        session_maker_bg = async_sessionmaker(
            bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
        )

        # Step 1: page programs
        async with session_maker_pbms() as session_pbms:
            total_count_result = await session_pbms.execute(
                select(func.count(G2PProgramDefinition.id))
            )
            total_count_result.scalar()
            g2p_program_definitions = (
                (
                    await session_pbms.execute(
                        select(G2PProgramDefinition).offset(offset).limit(page_size)
                    )
                )
                .scalars()
                .all()
            )
        _logger.info(
            f"Found {len(g2p_program_definitions)} programs in page {current_page} with page size {page_size}"
        )
        # Step 2: for each program, find latest approved list and check membership
        benefit_programs: List[BenefitProgram] = []
        async with session_maker_pbms() as session_pbms, session_maker_bg() as session_bg:
            for g2p_program_definition in g2p_program_definitions:
                am_i_enrolled, enrolment_date = await self._get_enrollment_status(
                    session_pbms, session_bg, g2p_program_definition.id, beneficiary_id
                )
                _logger.info(
                    f"Program {g2p_program_definition.program_mnemonic}: am_i_enrolled={am_i_enrolled}, enrolment_date={enrolment_date}"
                )
                # fetch benefit codes for this program
                g2p_benefit_codes_from_db = (
                    await session_pbms.execute(
                        select(
                            G2PBenefitCodes.id,
                            G2PBenefitCodes.benefit_mnemonic,
                            G2PBenefitCodes.benefit_type,
                            G2PBenefitCodes.benefit_description,
                            G2PBenefitCodes.measurement_unit,
                            G2PProgramBenefitCodes.max_quantity,
                        )
                        .join(
                            G2PProgramBenefitCodes,
                            G2PProgramBenefitCodes.benefit_code_id
                            == G2PBenefitCodes.id,
                        )
                        .where(
                            G2PProgramBenefitCodes.program_id
                            == g2p_program_definition.id
                        )
                    )
                ).all()
                _logger.info(
                    f"Found {len(g2p_benefit_codes_from_db)} benefit codes for program {g2p_program_definition.program_mnemonic}"
                )
                benefit_codes = [
                    {
                        "id": benefit_code.id,
                        "benefit_code_mnemonic": benefit_code.benefit_mnemonic,
                        "benefit_type": benefit_code.benefit_type,
                        "benefit_code_description": benefit_code.benefit_description,
                        "benefit_code_max_quantity": benefit_code.max_quantity,
                        "measurement_unit": benefit_code.measurement_unit,
                    }
                    for benefit_code in g2p_benefit_codes_from_db
                ]

                if am_i_enrolled:
                    benefit_programs.append(
                        BenefitProgram(
                            id=g2p_program_definition.id,
                            program_name=g2p_program_definition.description,
                            program_mnemonic=g2p_program_definition.program_mnemonic,
                            program_description=g2p_program_definition.description,
                            am_i_enrolled=True,
                            enrolment_date=enrolment_date,
                            benefit_codes=benefit_codes,
                        )
                    )

        # pagination reflects only enrolled programs in the current page window
        total_count = len(benefit_programs)
        total_pages = (total_count + page_size - 1) // page_size

        return await self.construct_benefit_program_success_response(
            benefit_program_request, benefit_programs, total_count, total_pages
        )

    async def construct_benefit_program_success_response(
        self,
        benefit_program_request: BenefitProgramRequest,
        benefit_programs: List[BenefitProgram],
        total_count: int = 0,
        total_pages: int = 0,
    ) -> BenefitProgramResponse:
        benefit_programs_response = BenefitProgramResponse(
            response_header={
                "request_id": benefit_program_request.request_header.request_id,
                "response_status": G2PResponseStatus.SUCCESS.value,
                "response_timestamp": datetime.now(),
            },
            response_body=BenefitProgramResponseBody(
                pagination_response={
                    "number_of_items": total_count,
                    "number_of_pages": total_pages,
                },
                response_payload=benefit_programs,
            ),
        )
        return benefit_programs_response

    async def construct_benefit_program_failure_response(
        self,
        benefit_program_request: BenefitProgramRequest,
        error_code: str,
        error_message: str | None = None,
    ) -> BenefitProgramResponse:
        benefit_programs_response = BenefitProgramResponse(
            response_header={
                "request_id": benefit_program_request.request_header.request_id,
                "response_status": G2PResponseStatus.ERROR.value,
                "response_error_code": error_code,
                "response_error_message": error_message,
                "response_timestamp": datetime.now(),
            },
            response_body=BenefitProgramResponseBody(
                pagination_response={
                    "number_of_items": 0,
                    "number_of_pages": 0,
                },
                response_payload=[],
            ),
        )
        return benefit_programs_response

    async def get_all_programs(
        self, beneficiary_id: str, benefit_program_request: BenefitProgramRequest
    ) -> BenefitProgramResponse:
        pagination = (
            benefit_program_request.request_body.pagination_request
            if benefit_program_request.request_body
            else None
        )

        # Extract pagination parameters
        page_size = pagination.page_size if pagination else 30
        current_page = pagination.current_page if pagination else 1
        offset = (current_page - 1) * page_size

        # Reuse the same PBMS queries and compute membership per program's latest approved list
        session_maker_pbms = async_sessionmaker(
            bind=_engine.get("db_engine_pbms"), expire_on_commit=False
        )
        session_maker_bg = async_sessionmaker(
            bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
        )

        async with session_maker_pbms() as session_pbms, session_maker_bg() as session_bg:
            # Count total programs
            total_count_result = await session_pbms.execute(
                select(func.count(G2PProgramDefinition.id))
            )
            total_count = total_count_result.scalar()
            total_pages = (total_count + page_size - 1) // page_size  # Ceiling division

            # Fetch paginated programs
            programs = (
                (
                    await session_pbms.execute(
                        select(G2PProgramDefinition).offset(offset).limit(page_size)
                    )
                )
                .scalars()
                .all()
            )

            if not programs:
                raise PBMSException(
                    code=PBMSErrorCodes.PROGRAM_NOT_FOUND,
                    message="No programs found",
                )

            # Benefit codes for all programs (not just paginated ones for efficiency)
            benefit_codes = (
                await session_pbms.execute(
                    select(
                        G2PProgramBenefitCodes.program_id,
                        G2PBenefitCodes.id,
                        G2PBenefitCodes.benefit_mnemonic,
                        G2PBenefitCodes.benefit_type,
                        G2PBenefitCodes.benefit_description,
                        G2PBenefitCodes.measurement_unit,
                        G2PProgramBenefitCodes.max_quantity,
                    ).join(
                        G2PBenefitCodes,
                        G2PProgramBenefitCodes.benefit_code_id == G2PBenefitCodes.id,
                    )
                )
            ).all()

            program_id_to_benefit_codes = {}
            for benefit_code in benefit_codes:
                program_id_to_benefit_codes.setdefault(
                    benefit_code.program_id, []
                ).append(
                    {
                        "id": benefit_code.id,
                        "benefit_code_mnemonic": benefit_code.benefit_mnemonic,
                        "benefit_type": benefit_code.benefit_type,
                        "benefit_code_description": benefit_code.benefit_description,
                        "benefit_code_max_quantity": benefit_code.max_quantity,
                        "measurement_unit": benefit_code.measurement_unit,
                    }
                )

            benefit_programs: List[BenefitProgram] = []
            for program in programs:
                am_i_enrolled, enrolment_date = await self._get_enrollment_status(
                    session_pbms, session_bg, program.id, beneficiary_id
                )

                benefit_programs.append(
                    BenefitProgram(
                        id=program.id,
                        program_name=program.description,
                        program_mnemonic=program.program_mnemonic,
                        program_description=program.description,
                        am_i_enrolled=am_i_enrolled,
                        enrolment_date=enrolment_date,
                        benefit_codes=program_id_to_benefit_codes.get(program.id, []),
                    )
                )

        return await self.construct_benefit_program_success_response(
            benefit_program_request, benefit_programs, total_count, total_pages
        )

    async def get_program(
        self, beneficiary_id: str, benefit_program_request: BenefitProgramRequest
    ) -> BenefitProgramDetailResponse:
        program_id = (
            benefit_program_request.request_body.request_payload.program_id
            if benefit_program_request.request_body
            and benefit_program_request.request_body.request_payload
            else None
        )
        if not program_id:
            return await self.construct_benefit_program_detail_failure_response(
                benefit_program_request,
                "INVALID_REQUEST",
                "program_id is required",
            )

        session_maker_pbms = async_sessionmaker(
            bind=_engine.get("db_engine_pbms"), expire_on_commit=False
        )
        async with session_maker_pbms() as session_pbms:
            program = (
                (
                    await session_pbms.execute(
                        select(G2PProgramDefinition).where(
                            G2PProgramDefinition.id == int(program_id)
                        )
                    )
                )
                .scalars()
                .first()
            )
            if not program:
                raise PBMSException(
                    code=PBMSErrorCodes.PROGRAM_NOT_FOUND,
                    message="Program not found",
                )
            _logger.info(f"Found program: {program.program_mnemonic}")
            # Determine latest approved list and membership for this program
            session_maker_bg_local = async_sessionmaker(
                bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
            )
            async with session_maker_bg_local() as session_bg_local:
                am_i_enrolled, enrolment_date = await self._get_enrollment_status(
                    session_pbms, session_bg_local, program.id, beneficiary_id
                )

            benefit_codes_from_db = (
                await session_pbms.execute(
                    select(
                        G2PBenefitCodes.id,
                        G2PBenefitCodes.benefit_mnemonic,
                        G2PBenefitCodes.benefit_type,
                        G2PBenefitCodes.benefit_description,
                        G2PBenefitCodes.measurement_unit,
                        G2PProgramBenefitCodes.max_quantity,
                    )
                    .join(
                        G2PProgramBenefitCodes,
                        G2PProgramBenefitCodes.benefit_code_id == G2PBenefitCodes.id,
                    )
                    .where(G2PProgramBenefitCodes.program_id == program.id)
                )
            ).all()

            benefit_codes = [
                {
                    "id": benefit_code.id,
                    "benefit_code_mnemonic": benefit_code.benefit_mnemonic,
                    "benefit_type": benefit_code.benefit_type,
                    "benefit_code_description": benefit_code.benefit_description,
                    "benefit_code_max_quantity": benefit_code.max_quantity,
                    "measurement_unit": benefit_code.measurement_unit,
                }
                for benefit_code in benefit_codes_from_db
            ]
            _logger.info(
                f"Found {len(benefit_codes)} benefit codes for program {program.program_mnemonic}"
            )
            benefit_program = BenefitProgram(
                id=program.id,
                program_name=program.description,
                program_mnemonic=program.program_mnemonic,
                program_description=program.description,
                am_i_enrolled=am_i_enrolled,
                enrolment_date=enrolment_date,
                benefit_codes=benefit_codes,
            )

        return await self.construct_benefit_program_detail_success_response(
            benefit_program_request, benefit_program
        )

    async def construct_benefit_program_detail_success_response(
        self,
        benefit_program_request: BenefitProgramRequest,
        benefit_program: BenefitProgram,
    ) -> BenefitProgramDetailResponse:
        return BenefitProgramDetailResponse(
            response_header={
                "request_id": benefit_program_request.request_header.request_id,
                "response_status": G2PResponseStatus.SUCCESS.value,
                "response_timestamp": datetime.now(),
            },
            response_body=BenefitProgramDetailResponseBody(
                response_payload=benefit_program
            ),
        )

    async def construct_benefit_program_detail_failure_response(
        self,
        benefit_program_request: BenefitProgramRequest,
        error_code: str,
        error_message: str | None = None,
    ) -> BenefitProgramDetailResponse:
        return BenefitProgramDetailResponse(
            response_header={
                "request_id": benefit_program_request.request_header.request_id,
                "response_status": G2PResponseStatus.ERROR.value,
                "response_error_code": error_code,
                "response_error_message": error_message,
                "response_timestamp": datetime.now(),
            },
            response_body=BenefitProgramDetailResponseBody(response_payload=None),
        )
