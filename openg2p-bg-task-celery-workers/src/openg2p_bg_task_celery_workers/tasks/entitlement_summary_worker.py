import logging
from datetime import datetime, timezone

from openg2p_bg_task_registry_adapters.factory import RegistryFactory
from openg2p_bg_task_registry_adapters.interface import RegistryInterface
from openg2p_pbms_models.models import (
    G2PBeneficiaryList,
    G2PProgramDefinition,
    StatusEnum,
)
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="entitlement_summary_worker")
def entitlement_summary_worker(id: int):
    _logger.info(
        "Starting entitlement summary generation request for beneficiary list id: %s",
        id,
    )
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
            beneficiary_list: G2PBeneficiaryList = (
                pbms_session.query(G2PBeneficiaryList)
                .filter(G2PBeneficiaryList.id == id)
                .first()
            )

            target_registry = (
                pbms_session.query(G2PProgramDefinition.target_registry)
                .filter(G2PProgramDefinition.id == beneficiary_list.program_id)
                .one_or_none()
            )
            target_registry = target_registry[0]

            try:
                registry_interface: RegistryInterface = (
                    RegistryFactory.get_registry_class(target_registry)
                )
                registry_interface.compute_entitlement_statistics(
                    beneficiary_list.beneficiary_list_id,
                    bg_task_session,
                    sr_session,
                )

                _logger.info(
                    f"Entitlement summary statistics added successfully for beneficiary list id: {id}"
                )

            except Exception as e:
                raise Exception(
                    f"Error computing entitlement summary statistics for beneficiary list id {id}: {e}"
                ) from e

            beneficiary_list.entitlement_number_of_attempts += 1
            beneficiary_list.entitlement_process_status = StatusEnum.complete.value
            beneficiary_list.entitlement_processed_date = datetime.now(timezone.utc)
            bg_task_session.commit()
            pbms_session.commit()

        except Exception as e:
            _logger.error(
                f"Error during processing entitlement request for beneficiary list id {id}: {str(e)}"
            )
            bg_task_session.rollback()
            pbms_session.rollback()

            beneficiary_list.entitlement_number_of_attempts += 1
            beneficiary_list.entitlement_processed_date = datetime.now(timezone.utc)
            beneficiary_list.entitlement_process_status = (
                StatusEnum.pending.value
                if beneficiary_list.entitlement_number_of_attempts
                < _config.worker_max_attempts
                else StatusEnum.failed.value
            )
            beneficiary_list.entitlement_latest_error_code = str(e)
            pbms_session.commit()

        _logger.info(
            f"Completed processing entitlements for beneficiary list details id: {id}"
        )
