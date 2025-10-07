# ruff: noqa: E402
import asyncio
import logging

from openg2p_bg_task_models.models import (
    BeneficiaryListDetails,
    DisbursementBatch,
    DisbursementEnvelope,
)
from openg2p_bg_task_registry_adapters.cache import init_cache
from openg2p_bg_task_registry_adapters.migrate import get_models
from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.context import dbengine
from sqlalchemy.ext.asyncio import create_async_engine

from .config import Settings
from .controllers import (
    BeneficiarySearchController,
    DisbursementController,
    SummaryController,
)
from .services import (
    BeneficiarySearchService,
    DisbursementBatchService,
    DisbursementEnvelopeService,
    SummaryService,
)

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()
        init_cache()
        SummaryService()
        BeneficiarySearchService()
        DisbursementBatchService()
        DisbursementEnvelopeService()
        SummaryController().post_init()
        DisbursementController().post_init()
        BeneficiarySearchController().post_init()

    def init_db(self):
        if _config.db_datasource:
            db_engine = create_async_engine(
                _config.db_datasource, echo=_config.db_logging
            )
            dbengine.set(db_engine)

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            _logger.info("Migrating database")
            await BeneficiaryListDetails.create_migrate()
            await DisbursementBatch.create_migrate()
            await DisbursementEnvelope.create_migrate()

            for model in get_models():
                await model.create_migrate()

        asyncio.run(migrate())
