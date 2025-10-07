from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="bg_task_celery_beat_", env_file=".env", extra="allow"
    )
    openapi_title: str = "OpenG2P PBMS Background Celery Tasks"
    openapi_description: str = """
        Celery Beat Producers for OpenG2P PBMS Background Task
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    # DB Driver Overwrite
    db_driver: str = "postgresql"

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

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"

    bg_task_worker_queue: str = "bg_task_worker_queue"

    producer_frequency: int = 30
    batch_size: int = 2000
    no_of_tasks_to_process: int = 5
