import logging

from sqlalchemy.ext.asyncio import create_async_engine

from .config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


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

        db_engine_bg_task = create_async_engine(_config.db_datasource)
        db_engine_sr = create_async_engine(db_datasource_sr)
        return {
            "db_engine_bg_task": db_engine_bg_task,
            "db_engine_sr": db_engine_sr,
        }
