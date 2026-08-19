import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.core.cache.redis import RedisManager
from app.core.config.settings import SETTINGS
from app.core.db.migrations import run_startup_schema_migrations
from app.core.db.session import dispose_db, init_db
from app.core.error import AuthException, ServiceException, service_exception_to_http
from app.core.mail.service import MAIL_SERVICE
from app.core.observability.health import HealthCheckResult, ReadinessResponse, get_readiness
from app.core.observability.logging import configure_request_context_logging, get_logger, mask_email
from app.core.observability.metrics import setup_metrics
from app.core.observability.request_context import (
    add_request_context_headers,
    reset_request_context,
    resolve_request_id,
    resolve_trace_id,
    set_request_context,
)
from app.core.observability.tracing import setup_tracing
from app.core.task_queue.services import TASK_QUEUE_BOOTSTRAP
from app.models.user import UserResponse, UserRole, Users
from app.routers.v1 import api_key, auth, events, github, webhooks
from app.utils.token import create_access_token

logger = get_logger("app.main")
BOOTSTRAP_USER: UserResponse | None = None
BOOTSTRAP_ACCESS_TOKEN: str | None = None


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, exc: ServiceException):
        http_exc = service_exception_to_http(exc)
        logger.error(
            "Service exception handled globally (method=%s, path=%s, status=%s, code=%s).",
            request.method,
            request.url.path,
            http_exc.status_code,
            exc.code.error,
        )
        return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})

    @app.exception_handler(Exception)
    async def default_exception_handler(_request, _exc):
        if isinstance(_exc, HTTPException):
            logger.error(
                "HTTP exception handled globally (status=%s, detail=%s).",
                _exc.status_code,
                _exc.detail,
            )
            return JSONResponse(status_code=_exc.status_code, content={"detail": _exc.detail})
        logger.exception("Unhandled server exception.")
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
        )


class AppConfigResponse(BaseModel):
    api_base_path: str
    login_enabled: bool
    password_auth_enabled: bool
    frontend_base_path: str
    email_enabled: bool
    oauth_enabled: bool
    oauth_providers: list[str]
    bootstrap_user: UserResponse | None = None
    bootstrap_access_token: str | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global BOOTSTRAP_USER, BOOTSTRAP_ACCESS_TOKEN
    if not SETTINGS.OAUTH_ENABLED:
        logger.info("OAuth integration is disabled.")
    else:
        logger.info(
            "OAuth integration enabled (providers=%s).",
            ",".join(SETTINGS.oauth_provider_list),
        )

    oauth_errors = SETTINGS.get_oauth_validation_errors()
    if oauth_errors:
        raise RuntimeError("Invalid OAuth configuration: " + " ".join(oauth_errors))
    if SETTINGS.OAUTH_ENABLED:
        logger.info("OAuth configuration validation succeeded.")

    await MAIL_SERVICE.initialize()
    await TASK_QUEUE_BOOTSTRAP.start_all()
    await run_startup_schema_migrations(SETTINGS.DATABASE_URL)
    logger.info("Database schema migration check complete (target=head).")
    await init_db()
    logger.info("Database initialization complete.")
    if not SETTINGS.LOGIN_ENABLED:
        bootstrap_email = SETTINGS.BOOTSTRAP_USER_EMAIL.strip().lower()
        bootstrap_name = SETTINGS.BOOTSTRAP_USER_NAME.strip()

        if bootstrap_email and bootstrap_name:
            bootstrap_user = await Users.get_user_response_by_email(bootstrap_email)
            if bootstrap_user is None:
                # Bootstrap user for login-disabled mode.
                try:
                    await Users.create_oauth_user(
                        email=bootstrap_email,
                        name=bootstrap_name,
                        provider="bootstrap",
                        identifier=bootstrap_email,
                        is_verified=True,
                        role=UserRole.ADMIN,
                    )
                except AuthException:
                    # Another startup worker may create it concurrently.
                    pass
                bootstrap_user = await Users.get_user_response_by_email(bootstrap_email)
                logger.info(
                    "Bootstrap user created (email=%s).",
                    mask_email(bootstrap_email),
                )
            else:
                logger.info(
                    "Bootstrap user found (email=%s).",
                    mask_email(bootstrap_email),
                )
            if bootstrap_user is not None and bootstrap_user.role != UserRole.ADMIN:
                bootstrap_user = await Users.update_user_role(
                    user_id=bootstrap_user.id,
                    role=UserRole.ADMIN,
                )
                logger.info(
                    "Bootstrap user role promoted to admin (email=%s).",
                    mask_email(bootstrap_email),
                )
            BOOTSTRAP_USER = bootstrap_user
            if bootstrap_user is not None:
                BOOTSTRAP_ACCESS_TOKEN = create_access_token(
                    subject=str(bootstrap_user.id),
                    email=bootstrap_user.email,
                )
                logger.info("Bootstrap access token issued (user_id=%s).", bootstrap_user.id)
            else:
                BOOTSTRAP_ACCESS_TOKEN = None
        else:
            BOOTSTRAP_USER = None
            BOOTSTRAP_ACCESS_TOKEN = None
            logger.warning(
                "Login is disabled but bootstrap user email/name is missing; bootstrap mode unavailable."
            )
    else:
        BOOTSTRAP_USER = None
        BOOTSTRAP_ACCESS_TOKEN = None
    logger.info("Application startup sequence complete.")
    try:
        yield
    finally:
        await TASK_QUEUE_BOOTSTRAP.stop_all()
        await dispose_db()
        await RedisManager.close()


def create_app() -> FastAPI:
    static_dist_dir = (Path(__file__).resolve().parent / "static" / "dist").resolve()
    log_level_name = SETTINGS.LOG_LEVEL.upper()
    log_level_value = logging.getLevelName(log_level_name)
    if not isinstance(log_level_value, int):
        log_level_name = "INFO"
        log_level_value = logging.INFO

    logging.getLogger("uvicorn.error").setLevel(log_level_value)
    logging.getLogger("uvicorn.access").setLevel(log_level_value)
    logging.getLogger("uvicorn").setLevel(log_level_value)
    configure_request_context_logging()

    app = FastAPI(
        title=SETTINGS.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if SETTINGS.SWAGGER_ENABLED else None,
        redoc_url="/redoc" if SETTINGS.SWAGGER_ENABLED else None,
        openapi_url="/openapi.json" if SETTINGS.SWAGGER_ENABLED else None,
    )

    logger.info("App log level set to %s.", log_level_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=SETTINGS.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Trace-ID"],
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = resolve_request_id(request)
        trace_id = resolve_trace_id(request)
        tokens = set_request_context(request_id=request_id, trace_id=trace_id)
        try:
            response = await call_next(request)
            add_request_context_headers(
                response,
                request_id=request_id,
                trace_id=trace_id,
            )
            return response
        finally:
            reset_request_context(tokens)

    register_exception_handlers(app)

    @app.get("/ping")
    async def ping():
        return {"status": "ok", "message": "pong"}

    @app.get("/health/live", response_model=HealthCheckResult, include_in_schema=False)
    async def health_live():
        return HealthCheckResult(status="ok")

    @app.get("/health/ready", response_model=ReadinessResponse, include_in_schema=False)
    async def health_ready():
        readiness = await get_readiness()
        if readiness.status != "ok":
            return JSONResponse(status_code=503, content=readiness.model_dump())
        return readiness

    @app.get("/config", response_model=AppConfigResponse)
    async def config():
        return {
            "api_base_path": "/api/v1",
            "login_enabled": SETTINGS.LOGIN_ENABLED,
            "password_auth_enabled": SETTINGS.PASSWORD_AUTH_ENABLED,
            "frontend_base_path": "",
            "email_enabled": SETTINGS.EMAIL_ENABLED,
            "oauth_enabled": SETTINGS.OAUTH_ENABLED,
            "oauth_providers": SETTINGS.oauth_provider_list if SETTINGS.OAUTH_ENABLED else [],
            "bootstrap_user": None if SETTINGS.LOGIN_ENABLED else BOOTSTRAP_USER,
            "bootstrap_access_token": None if SETTINGS.LOGIN_ENABLED else BOOTSTRAP_ACCESS_TOKEN,
        }

    setup_metrics(app)
    setup_tracing(app)

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(api_key.router, prefix="/api/v1/api-keys", tags=["API Keys"])
    app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
    app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub"])
    app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

    if static_dist_dir.exists():
        app.mount("/", StaticFiles(directory=static_dist_dir, html=True), name="frontend")

        @app.exception_handler(404)
        async def spa_fallback(request: Request, exc):
            accepts_html = "text/html" in request.headers.get("accept", "")
            is_api_path = request.url.path.startswith("/api/")
            if request.method in {"GET", "HEAD"} and accepts_html and not is_api_path:
                index_path = static_dist_dir / "index.html"
                if index_path.exists():
                    return FileResponse(index_path)

            # Preserve API error payload shape for domain 404 responses.
            if is_api_path:
                detail = getattr(exc, "detail", "Not Found")
                return JSONResponse(status_code=404, content={"detail": detail})

            return JSONResponse(status_code=404, content={"detail": "Not Found"})

    return app


app = create_app()
