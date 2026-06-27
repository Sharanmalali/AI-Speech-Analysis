"""FastAPI application factory and entrypoint for AblePro Solutions.

Wires together configuration, logging, middleware, exception handlers,
rate limiting, routers and the model-warmup lifespan. Import-safe: heavy
ML services are loaded lazily inside the lifespan so the module can be
imported in test/tooling contexts without the full ML stack installed.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.config import settings
from app.core.exceptions import RateLimitError, register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import limiter
from app.routers.health import router as health_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: warm models on startup, release on shutdown."""
    configure_logging()
    logger.info(
        "startup",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )

    # Warm ML services once at startup so the first request is fast.
    # Guarded so the API can still boot in environments where the heavy ML
    # stack (torch/pyannote/whisper) is intentionally absent.
    try:
        from app.services.ml.registry import warmup_models

        warmup_models()
    except Exception as exc:  # noqa: BLE001
        logger.warning("model_warmup_skipped", error=str(exc))

    yield

    logger.info("shutdown", app=settings.APP_NAME)


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    configure_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ----- Rate limiting -----------------------------------------------------
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(_, exc: RateLimitExceeded):  # type: ignore[no-untyped-def]
        err = RateLimitError(details={"limit": str(exc.limit.limit)})
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=err.status_code, content=err.to_payload())

    app.add_middleware(SlowAPIMiddleware)

    # ----- Compression -------------------------------------------------------
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # ----- CORS --------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )

    # ----- Exception handlers ------------------------------------------------
    register_exception_handlers(app)

    # ----- Routers -----------------------------------------------------------
    app.include_router(health_router)
    _register_api_routers(app)

    return app


def _register_api_routers(app: FastAPI) -> None:
    """Include versioned API routers.

    Each router is imported independently so that a router introduced in a
    later build phase (or one whose optional deps are missing) cannot prevent
    the others from loading.
    """
    prefix = settings.API_V1_PREFIX
    for module_name in ("auth", "upload", "jobs", "results", "reports", "admin"):
        try:
            module = __import__(f"app.routers.{module_name}", fromlist=["router"])
            app.include_router(module.router, prefix=prefix)
            logger.info("router_registered", router=module_name)
        except ImportError as exc:
            logger.warning("router_not_loaded", router=module_name, error=str(exc))


app = create_app()
