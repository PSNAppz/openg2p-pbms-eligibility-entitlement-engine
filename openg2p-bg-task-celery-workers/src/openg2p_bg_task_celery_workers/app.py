# ruff: noqa: E402

import logging

from .config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)

from celery import Celery
from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.exception import BaseExceptionHandler
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine


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
        db_datasource_bg_task_async = construct_db_datasource(
            _config.db_driver_async,
            _config.db_username_async,
            _config.db_password_async,
            _config.db_hostname_async,
            _config.db_port_async,
            _config.db_dbname_async,
        )
        db_engine_bg_task = create_engine(_config.db_datasource)
        db_engine_sr = create_engine(db_datasource_sr)
        db_engine_pbms = create_engine(db_datasource_pbms)
        db_engine_bg_task_async = create_async_engine(db_datasource_bg_task_async)
        return {
            "db_engine_bg_task": db_engine_bg_task,
            "db_engine_sr": db_engine_sr,
            "db_engine_pbms": db_engine_pbms,
            "db_engine_bg_task_async": db_engine_bg_task_async,
        }


celery_app = Celery(
    "g2p_bg_task_celery_worker",
    broker=_config.celery_broker_url,
    backend=_config.celery_backend_url,
    include=["openg2p_bg_task_celery_workers.tasks"],
)

celery_app.conf.timezone = "UTC"
