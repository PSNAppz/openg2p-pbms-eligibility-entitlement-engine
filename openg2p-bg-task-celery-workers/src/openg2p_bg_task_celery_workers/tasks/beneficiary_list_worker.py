import json
import logging
from datetime import datetime, timezone
from typing import List

from openg2p_bg_task_models.models import BeneficiaryListDetails, BeneficiaryListSummary
from openg2p_bg_task_models.schemas import RegistrantDetails
from openg2p_bg_task_registry_adapters.factory import RegistryFactory
from openg2p_bg_task_registry_adapters.interface import RegistryInterface
from openg2p_pbms_models.models import (
    G2PBeneficiaryList,
    G2PEligibilityRuleDefinition,
    G2PPriorityRuleDefinition,
    G2PProgramDefinition,
    ListStageEnum,
    ListWorkflowStatusEnum,
    StatusEnum,
)
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from ..helpers import (
    construct_eligibility_query,
    construct_priority_query,
)

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="beneficiary_list_worker")
def beneficiary_list_worker(id: int):
    _logger.info("Starting eligibility list generation for beneficiary list id: %s", id)
    bg_task_session_maker = sessionmaker(
        bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
    )
    sr_session_maker = sessionmaker(
        bind=_engine.get("db_engine_sr"), expire_on_commit=False
    )
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )

    with bg_task_session_maker() as bg_task_session, sr_session_maker() as sr_session, pbms_session_maker() as pbms_session:
        beneficiary_list = None
        try:
            # Fetch the queue entry from pbms db using id
            beneficiary_list = (
                pbms_session.query(G2PBeneficiaryList)
                .filter(G2PBeneficiaryList.id == id)
                .first()
            )
            g2p_program_definition = (
                pbms_session.query(G2PProgramDefinition)
                .filter(G2PProgramDefinition.id == beneficiary_list.program_id)
                .first()
            )

            constructed_query = None

            if beneficiary_list.list_stage == ListStageEnum.ENROLLMENT.value:
                _logger.info(
                    "Constructing enrollment sql query for beneficiary list id: %s", id
                )
                constructed_query = construct_enrollment_sql_query(
                    pbms_session, beneficiary_list
                )
            elif beneficiary_list.list_stage == ListStageEnum.DISBURSEMENT.value:
                _logger.info(
                    "Constructing disbursement sql query for beneficiary list id: %s",
                    id,
                )
                constructed_query = construct_disbursement_sql_query(
                    pbms_session, bg_task_session, beneficiary_list
                )
            else:
                _logger.error(
                    f"Invalid list stage {beneficiary_list.list_stage} for beneficiary list id {id}"
                )
            _logger.debug(
                f"Constructed sql query for beneficiary list id {id} is: {constructed_query}"
            )

            # Execute the constructed SQL query to fetch registrant details and build BeneficiaryListDetails objects
            total_number_of_registrants = 0
            beneficiary_list_details: List[BeneficiaryListDetails] = []
            registry_cursor = sr_session.execute(constructed_query)
            while True:
                number_of_registrants_for_batch = 0
                registry_batch = registry_cursor.fetchmany(_config.batch_size)
                registrant_details: List[RegistrantDetails] = []
                if not registry_batch:
                    break
                for registry_row in registry_batch:
                    number_of_registrants_for_batch += 1
                    registrant_details.append(
                        RegistrantDetails(
                            registrant_id=registry_row[0],
                            entitlement={},
                            compute_elements={},
                        ).model_dump(mode="json")
                    )

                total_number_of_registrants += number_of_registrants_for_batch
                beneficiary_list_details.append(
                    BeneficiaryListDetails(
                        beneficiary_list_id=beneficiary_list.beneficiary_list_id,
                        registrant_details=registrant_details,
                        entitlement_process_status=StatusEnum.pending.value
                        if beneficiary_list.list_stage
                        == ListStageEnum.DISBURSEMENT.value
                        else StatusEnum.not_applicable.value,
                        number_of_registrants=number_of_registrants_for_batch,
                    )
                )
            _logger.debug(
                f"Count of registrant IDs for beneficiary list id {id} are: {total_number_of_registrants}"
            )
            beneficiary_list.number_of_registrants = total_number_of_registrants

            _logger.info(f"Adding eligibility details for beneficiary list id: {id}")
            bg_task_session.add_all(beneficiary_list_details)

            _logger.info(
                f"Computing and adding summary statistics for beneficiary list id: {id}"
            )
            # Create base summary object
            base_summary = BeneficiaryListSummary(
                program_id=beneficiary_list.program_id,
                program_mnemonic=g2p_program_definition.program_mnemonic,
                target_registry=g2p_program_definition.target_registry,
                beneficiary_list_id=beneficiary_list.beneficiary_list_id,
                number_of_registrants=total_number_of_registrants,
                date_created=datetime.now(timezone.utc),
            )
            _logger.debug(
                f"Base summary for beneficiary list id {id} is: {base_summary}"
            )

            try:
                # Get the appropriate summary computation class
                summary_computation_interface: RegistryInterface = (
                    RegistryFactory.get_registry_class(
                        g2p_program_definition.target_registry
                    )
                )

                # Compute summary and add to session
                summary_computation_interface.compute_eligibility_statistics(
                    beneficiary_list_details, base_summary, sr_session, bg_task_session
                )

                _logger.info(
                    f"Summary statistics added successfully for beneficiary list id: {id}"
                )

            except ValueError as e:
                raise Exception(
                    f"Invalid registrant type for program_id {beneficiary_list.program_id}: {e}"
                ) from e

            except Exception as e:
                raise Exception(
                    f"Error computing summary statistics for beneficiary list id {id}: {e}"
                ) from e

            # Update beneficiary list entry status
            beneficiary_list.eligibility_process_status = StatusEnum.complete.value

            if beneficiary_list.list_stage == ListStageEnum.DISBURSEMENT.value:
                beneficiary_list.entitlement_process_status = StatusEnum.pending.value

            beneficiary_list.processed_date = datetime.now(timezone.utc)

            bg_task_session.commit()
            pbms_session.commit()

        except Exception as e:
            _logger.error(
                "Error during processing eligibility request for beneficiary list id {}: {}".format(
                    id, str(e)
                )
            )
            # Rollback all sessions
            pbms_session.rollback()
            bg_task_session.rollback()

            beneficiary_list.eligibility_number_of_attempts += 1
            beneficiary_list.eligibility_processed_date = datetime.now(timezone.utc)
            beneficiary_list.eligibility_process_status = (
                StatusEnum.pending.value
                if beneficiary_list.eligibility_number_of_attempts
                < _config.worker_max_attempts
                else StatusEnum.failed.value
            )
            beneficiary_list.eligibility_latest_error_code = str(e)
            pbms_session.commit()
            raise e

        _logger.info(
            "Completed processing eligibility request for beneficiary list id: %s" % id
        )


def construct_enrollment_sql_query(pbms_session, beneficiary_list):
    sql_queries_and_set_operators = pbms_session.execute(
        select(
            G2PEligibilityRuleDefinition.sql_query,
            G2PEligibilityRuleDefinition.set_operator,
        )
        .where(G2PEligibilityRuleDefinition.program_id == beneficiary_list.program_id)
        .order_by(G2PEligibilityRuleDefinition.rule_number.asc())
    ).all()

    return construct_eligibility_query(sql_queries_and_set_operators)


def construct_disbursement_sql_query(pbms_session, bg_task_session, beneficiary_list):
    # Get the beneficiary_list_id of the latest APPROVED FINAL ENROLMENT in the same program
    latest_approved_final_enrollment_beneficiary_list_id = (
        pbms_session.query(G2PBeneficiaryList.beneficiary_list_id)
        .filter(
            G2PBeneficiaryList.program_id == beneficiary_list.program_id,
            G2PBeneficiaryList.list_stage == ListStageEnum.ENROLLMENT.value,
            G2PBeneficiaryList.list_workflow_status
            == ListWorkflowStatusEnum.APPROVED_FINAL_ENROLMENT.value,
        )
        .order_by(G2PBeneficiaryList.creation_date.desc())
        .first()
    )
    if latest_approved_final_enrollment_beneficiary_list_id:
        latest_approved_final_enrollment_beneficiary_list_id = (
            latest_approved_final_enrollment_beneficiary_list_id[0]
        )

    # Get the registrant_details field from beneficiary_list_details for the latest approved final enrollment
    registrant_details_list = None
    if latest_approved_final_enrollment_beneficiary_list_id:
        registrant_details_list = (
            bg_task_session.execute(
                select(BeneficiaryListDetails.registrant_details).where(
                    BeneficiaryListDetails.beneficiary_list_id
                    == latest_approved_final_enrollment_beneficiary_list_id
                )
            )
            .scalars()
            .all()
        )

    # Get approved registrant details for the latest approved final enrollment
    registrant_ids = []
    for registrant_details in registrant_details_list:
        if registrant_details:
            if isinstance(registrant_details, str):
                registrant_details = json.loads(registrant_details)
            registrant_ids = [
                registrant["registrant_id"] for registrant in registrant_details
            ]

    # Fetch priority rule SQL queries for the current disbursement cycle and construct the priority query using the list of registrant IDs
    sql_queries = (
        pbms_session.execute(
            select(G2PPriorityRuleDefinition.sql_query).where(
                G2PPriorityRuleDefinition.disbursement_cycle_id
                == beneficiary_list.disbursement_cycle_id
            )
        )
        .scalars()
        .all()
    )
    return (
        construct_priority_query(sql_queries, registrant_ids)
        if sql_queries
        else construct_enrollment_sql_query(pbms_session, beneficiary_list)
    )
