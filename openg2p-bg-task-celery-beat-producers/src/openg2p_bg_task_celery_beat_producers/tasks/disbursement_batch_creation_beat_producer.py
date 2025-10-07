import logging

from openg2p_pbms_models.models import (
    G2PBeneficiaryList,
    ListStageEnum,
    ListWorkflowStatusEnum,
    StatusEnum,
)
from sqlalchemy import and_, select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from .worker_types import WorkerTypes

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="disbursement_batch_creation_beat_producer")
def disbursement_batch_creation_beat_producer():
    _logger.info("Checking for pending disbursement requests")
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )

    with pbms_session_maker() as pbms_session:
        beneficiary_lists = (
            pbms_session.execute(
                select(G2PBeneficiaryList)
                .where(
                    and_(
                        G2PBeneficiaryList.list_workflow_status
                        == ListWorkflowStatusEnum.APPROVED_FOR_DISBURSEMENT.value,
                        G2PBeneficiaryList.list_stage
                        == ListStageEnum.DISBURSEMENT.value,
                        G2PBeneficiaryList.envelope_creation_status
                        == StatusEnum.complete.value,
                        G2PBeneficiaryList.disbursement_batch_creation_status
                        == StatusEnum.pending.value,
                    )
                )
                .limit(_config.no_of_tasks_to_process)
            )
            .scalars()
            .all()
        )

        for beneficiary_list in beneficiary_lists:
            beneficiary_list.disbursement_batch_creation_status = (
                StatusEnum.processing.value
            )
            worker_type = WorkerTypes.DISBURSEMENT_BATCH_CREATION_WORKER
            celery_app.send_task(
                worker_type,
                args=(beneficiary_list.id,),
                queue=_config.bg_task_worker_queue,
            )

            pbms_session.commit()
            _logger.info(
                f"Sent task to {worker_type} for Beneficiary List ID: {beneficiary_list.id}"
            )

    _logger.info(
        "Completed processing pending disbursement enevelope creation requests"
    )
