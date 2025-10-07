import logging
from typing import List

from openg2p_bg_task_models.models import BeneficiaryListDetails
from openg2p_pbms_models.models import StatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from .worker_types import WorkerTypes

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="entitlement_beat_producer")
def entitlement_beat_producer():
    _logger.info("Checking for pending entitlement requests in BeneficiaryListDetails")
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )
    bg_task_session_maker = sessionmaker(
        bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
    )
    with bg_task_session_maker() as bg_task_session, pbms_session_maker():
        beneficiary_list_details: List[BeneficiaryListDetails] = (
            bg_task_session.execute(
                select(BeneficiaryListDetails)
                .filter(
                    # BeneficiaryListDetails.beneficiary_list_id == beneficiary_list.beneficiary_list_id,
                    BeneficiaryListDetails.entitlement_process_status
                    == StatusEnum.pending.value
                )
                .limit(_config.no_of_tasks_to_process)
            )
            .scalars()
            .all()
        )
        _logger.info(
            f"Found {len(beneficiary_list_details)} pending entitlement requests"
        )

        for beneficiary_list_detail in beneficiary_list_details:
            _logger.info(
                f"Queueing entitlement for Benficiary List ID: {beneficiary_list_detail.id}"
            )

            beneficiary_list_detail.entitlement_process_status = (
                StatusEnum.processing.value
            )
            bg_task_session.add(beneficiary_list_detail)

            _logger.info(
                f"Updating status for {WorkerTypes.ENTITLEMENT_WORKER} to processing in Benficiary List Details ID: {beneficiary_list_detail.id}"
            )

            # Send task to appropriate celery worker
            celery_app.send_task(
                WorkerTypes.ENTITLEMENT_WORKER,
                args=(beneficiary_list_detail.id,),
                queue=_config.bg_task_worker_queue,
            )
            _logger.info(
                f"Sent task to {WorkerTypes.ENTITLEMENT_WORKER} for beneficiary list details id: {beneficiary_list_detail.id}"
            )
        bg_task_session.commit()

    _logger.info(
        "Completed processing pending entitlement requests in BeneficiaryListDetails"
    )
