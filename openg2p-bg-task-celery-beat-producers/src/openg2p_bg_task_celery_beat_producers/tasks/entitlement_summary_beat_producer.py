import logging
from typing import List

from openg2p_bg_task_models.models import BeneficiaryListDetails
from openg2p_pbms_models.models import G2PBeneficiaryList, StatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from .worker_types import WorkerTypes

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="entitlement_summary_beat_producer")
def entitlement_summary_beat_producer():
    _logger.info("Checking for pending entitlement summary computaion requests")
    bg_task_session_maker = sessionmaker(
        bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
    )
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )
    with pbms_session_maker() as pbms_session, bg_task_session_maker() as bg_task_session:
        beneficiary_lists: List[G2PBeneficiaryList] = (
            pbms_session.execute(
                select(G2PBeneficiaryList)
                .filter(
                    G2PBeneficiaryList.entitlement_process_status
                    == StatusEnum.pending.value
                )
                .limit(_config.no_of_tasks_to_process)
            )
            .scalars()
            .all()
        )
        _logger.info(
            f"Found {len(beneficiary_lists)} pending entitlement summary requests"
        )

        for beneficiary_list in beneficiary_lists:
            beneficiary_list_details: List[BeneficiaryListDetails] = (
                bg_task_session.query(BeneficiaryListDetails)
                .filter(
                    BeneficiaryListDetails.beneficiary_list_id
                    == beneficiary_list.beneficiary_list_id
                )
                .all()
            )
            if beneficiary_list_details and all(
                beneficiary_list_detail.entitlement_process_status
                == StatusEnum.complete.value
                for beneficiary_list_detail in beneficiary_list_details
            ):
                # Send task to appropriate celery worker
                celery_app.send_task(
                    WorkerTypes.ENTITLEMENT_SUMMARY_WORKER,
                    args=(beneficiary_list.id,),
                    queue=_config.bg_task_worker_queue,
                )
                _logger.info(
                    f"Sent task to {WorkerTypes.ENTITLEMENT_SUMMARY_WORKER} for beneficiary_list_id: {beneficiary_list.id}"
                )

                beneficiary_list.entitlement_process_status = (
                    StatusEnum.processing.value
                )

                _logger.info(
                    f"Updating status for {WorkerTypes.BENEFICIARY_LIST_WORKER} to processing in beneficiary list id: {beneficiary_list.id}"
                )
        pbms_session.commit()

    _logger.info(
        "Completed processing pending entitlement summary requests for beneficiary lists"
    )
