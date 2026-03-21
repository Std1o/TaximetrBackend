import logging

from fastapi import FastAPI

from taximetr.api import router

logger = logging.getLogger(__name__)


# Создаем приложение с lifespan
app = FastAPI(
    max_request_size=None,
)
app.include_router(router)