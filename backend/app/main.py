from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.routes import create_api_router
from app.core import configure_logging, settings
from app.db import Database
from app.services import FactoryAgentService, FactoryDataService


configure_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_title, version=settings.app_version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    database = Database()
    data_service = FactoryDataService(database)
    agent_service = FactoryAgentService(data_service)
    app.include_router(create_api_router(data_service, agent_service))

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            logger.exception(
                "request_failed request_id=%s method=%s path=%s client=%s",
                request_id,
                request.method,
                request.url.path,
                request.client.host if request.client else "",
            )
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "request_completed request_id=%s method=%s path=%s status=%s duration_ms=%.2f client=%s",
                request_id,
                request.method,
                request.url.path,
                status_code,
                elapsed_ms,
                request.client.host if request.client else "",
            )

    return app


app = create_app()
