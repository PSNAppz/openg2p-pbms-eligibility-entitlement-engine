# ruff: noqa: E402

import logging

from celery import Celery
from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.exception import BaseExceptionHandler
from sqlalchemy import create_engine

from .config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().init_logger()
        super().init_app()
        BaseExceptionHandler()


def construct_db_datasource(
    db_driver, db_username, db_password, db_hostname, db_port, db_dbname
) -> str:
    datasource = ""
    if db_driver:
        datasource += f"{db_driver}://"
    if db_username:
        datasource += f"{db_username}:{db_password}@"
    if db_hostname:
        datasource += db_hostname
    if db_port:
        datasource += f":{db_port}"
    if db_dbname:
        datasource += f"/{db_dbname}"

    _logger.info(f"Constructed Datasource: {datasource}")

    return datasource


def get_engine():
    if _config.db_datasource:
        db_datasource_sr = construct_db_datasource(
            _config.db_driver,
            _config.db_username_sr,
            _config.db_password_sr,
            _config.db_hostname_sr,
            _config.db_port_sr,
            _config.db_dbname_sr,
        )
        db_datasource_pbms = construct_db_datasource(
            _config.db_driver,
            _config.db_username_pbms,
            _config.db_password_pbms,
            _config.db_hostname_pbms,
            _config.db_port_pbms,
            _config.db_dbname_pbms,
        )
        db_engine_bg_task = create_engine(_config.db_datasource)
        db_engine_sr = create_engine(db_datasource_sr)
        db_engine_pbms = create_engine(db_datasource_pbms)
        return {
            "db_engine_bg_task": db_engine_bg_task,
            "db_engine_sr": db_engine_sr,
            "db_engine_pbms": db_engine_pbms,
        }


celery_app = Celery(
    "g2p_bg_task_celery_beat_producer",
    broker=_config.celery_broker_url,
    backend=_config.celery_backend_url,
    include=["openg2p_bg_task_celery_beat_producers.tasks"],
)

celery_app.conf.beat_schedule = {
    "beneficiary_list_beat_producer": {
        "task": "beneficiary_list_beat_producer",
        "schedule": _config.producer_frequency,
    },
    "entitlement_beat_producer": {
        "task": "entitlement_beat_producer",
        "schedule": _config.producer_frequency,
    },
    "entitlement_summary_beat_producer": {
        "task": "entitlement_summary_beat_producer",
        "schedule": _config.producer_frequency,
    },
    "disbursement_envelope_creation_beat_producer": {
        "task": "disbursement_envelope_creation_beat_producer",
        "schedule": _config.producer_frequency,
    },
    "disbursement_batch_creation_beat_producer": {
        "task": "disbursement_batch_creation_beat_producer",
        "schedule": _config.producer_frequency,
    },
    "disbursement_beat_producer": {
        "task": "disbursement_beat_producer",
        "schedule": _config.producer_frequency,
    },
}
celery_app.conf.timezone = "UTC"
