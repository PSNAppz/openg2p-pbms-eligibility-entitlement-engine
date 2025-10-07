from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="bg_task_celery_workers_", env_file=".env", extra="allow"
    )
    openapi_title: str = "OpenG2P PBMS Background Task Celery Workers"
    openapi_description: str = """
        Celery workers for OpenG2P PBMS Background Task
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    # DB Driver Overwrite
    db_driver: str = "postgresql"

    # BG Task Database
    db_username: str = "postgres"
    db_password: str = "postgres"
    db_hostname: str = "localhost"
    db_port: int = 5432
    db_dbname: str = "bgtaskdb"

    # Social Registry Database
    db_username_sr: str = "postgres"
    db_password_sr: str = "postgres"
    db_hostname_sr: str = "localhost"
    db_port_sr: int = 5432
    db_dbname_sr: str = "socialregistrydb"

    # PBMS Database
    db_username_pbms: str = "postgres"
    db_password_pbms: str = "postgres"
    db_hostname_pbms: str = "localhost"
    db_port_pbms: int = 5432
    db_dbname_pbms: str = "pbmsdb"

    # Background Task Database (async)
    db_driver_async: str = "postgresql+asyncpg"
    db_username_async: str = "postgres"
    db_password_async: str = "postgres"
    db_hostname_async: str = "localhost"
    db_port_async: int = 5432
    db_dbname_async: str = "bgtaskdb"

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"

    g2p_bridge_base_url: str = "http://g2pbridge-api"

    batch_size: int = 2000
    worker_max_attempts: int = 5

    sign_key_keymanager_app_id: str = "PBMS"
    sign_key_keymanager_ref_id: str = ""

    keymanager_api_timeout: int = 10
    keymanager_api_base_url: str = ""
    keymanager_auth_enabled: bool = True

    # TODO: auth -> oauth, remove 'keymanager'
    keymanager_auth_url: str = ""
    keymanager_auth_client_id: str = "openg2p-pbms"
    keymanager_auth_client_secret: str = ""
