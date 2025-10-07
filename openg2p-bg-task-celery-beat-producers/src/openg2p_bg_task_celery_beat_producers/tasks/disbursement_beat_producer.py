import logging
from typing import List

from openg2p_bg_task_models.models import DisbursementBatch
from openg2p_pbms_models.models import StatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from .worker_types import WorkerTypes

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="disbursement_beat_producer")
def disbursement_beat_producer():
    _logger.info("Checking for pending disbursement batch status requests")
    bg_task_session_maker = sessionmaker(
        bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
    )

    with bg_task_session_maker() as bg_task_session:
        disbursement_batches: List[DisbursementBatch] = (
            bg_task_session.execute(
                select(DisbursementBatch)
                .filter(
                    DisbursementBatch.disbursement_status == StatusEnum.pending.value
                )
                .order_by(DisbursementBatch.id)
                .limit(_config.no_of_tasks_to_process)
            )
            .scalars()
            .all()
        )
        _logger.debug(
            f"Found {len(disbursement_batches)} pending disbursement batch requests"
        )

        for disbursement_batch in disbursement_batches:
            _logger.info(f"Queueing Disbursement Batch ID: {disbursement_batch.id}")

            # Update the status to processing
            disbursement_batch.disbursement_status = StatusEnum.processing.value
            _logger.info(
                f"Updating status for Disbursement Batch ID: {disbursement_batch.id} to processing"
            )
            bg_task_session.commit()
            worker_type = WorkerTypes.DISBURSEMENT_WORKER
            # Send task to the appropriate celery worker
            celery_app.send_task(
                worker_type,
                args=(disbursement_batch.id,),
                queue=_config.bg_task_worker_queue,
            )
            _logger.info(
                f"Sent task to {worker_type} for Disbursement Batch ID: {disbursement_batch.id}"
            )

    _logger.info("Completed processing pending Disbursement Batch requests")
