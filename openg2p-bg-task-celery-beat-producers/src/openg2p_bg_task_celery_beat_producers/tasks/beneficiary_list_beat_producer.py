import logging
from typing import List

from openg2p_pbms_models.models import G2PBeneficiaryList, StatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from .worker_types import WorkerTypes

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="beneficiary_list_beat_producer")
def beneficiary_list_beat_producer():
    _logger.info("Checking for pending beneficiary list requests")
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )
    with pbms_session_maker() as pbms_session:
        # Fetch rows with pending status
        beneficiary_lists: List[G2PBeneficiaryList] = (
            pbms_session.execute(
                select(G2PBeneficiaryList)
                .filter(
                    G2PBeneficiaryList.eligibility_process_status
                    == StatusEnum.pending.value
                )
                .limit(_config.no_of_tasks_to_process)
            )
            .scalars()
            .all()
        )
        _logger.info(f"Found {len(beneficiary_lists)} pending eligibility requests")

        for beneficiary_list in beneficiary_lists:
            _logger.info(f"Queueing beneficiary list id: {beneficiary_list.id}")

            beneficiary_list.eligibility_process_status = StatusEnum.processing.value
            pbms_session.add(beneficiary_list)

            _logger.info(
                f"Updating status for {WorkerTypes.BENEFICIARY_LIST_WORKER} to processing in beneficiary list id: {beneficiary_list.id}"
            )

            # Send task to appropriate celery worker
            celery_app.send_task(
                WorkerTypes.BENEFICIARY_LIST_WORKER,
                args=(beneficiary_list.id,),
                queue=_config.bg_task_worker_queue,
            )
            _logger.info(
                f"Sent task to {WorkerTypes.BENEFICIARY_LIST_WORKER} for beneficiary_list_id: {beneficiary_list.id}"
            )
        pbms_session.commit()

    _logger.info("Completed processing pending beneficiary lists")
