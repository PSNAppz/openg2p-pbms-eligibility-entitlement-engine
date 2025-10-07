from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="pbms_bene_portal_api_", env_file=".env", extra="allow"
    )

    openapi_title: str = "OpenG2P PBMS Bene Portal API"
    openapi_description: str = """
        FastAPI Service for OpenG2P PBMS Bene Portal API
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    # PBMS Database
    db_username_pbms: str = "postgres"
    db_password_pbms: str = "password"
    db_hostname_pbms: str = "localhost"
    db_port_pbms: int = 5432
    db_dbname_pbms: str = "pbmsdb"

    # BG Task Database
    db_username_bg_task: str = "postgres"
    db_password_bg_task: str = "password"
    db_hostname_bg_task: str = "localhost"
    db_port_bg_task: int = 5432
    db_dbname_bg_task: str = "bg_taskdb"
