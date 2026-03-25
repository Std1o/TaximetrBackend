import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from taximetr.api import router
from taximetr.database import Session
from taximetr.service.tariffs import TariffService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = Session()  # Создаем сессию через sessionmaker
    try:
        tariff_service = TariffService(db)
        tariff_service.init_default_tariffs()
        logger.info("Tariffs initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing tariffs: {e}")
    finally:
        db.close()

    yield

    # Shutdown (если нужно)
    pass


app = FastAPI(
    max_request_size=None,
    lifespan=lifespan
)
app.include_router(router)