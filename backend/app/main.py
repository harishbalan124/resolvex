from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.limiter import limiter
from app.core.logging import logger, mask_sensitive_data


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description=(
            "Enterprise Customer Experience Intelligence & Autonomous Dispute Resolution "
            f"powered by {settings.AI_ENGINE_NAME}."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Attach rate limiter
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Configure CORS
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Global Exception Handler protecting sensitive PII
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        raw_error = str(exc)
        sanitized_error = mask_sensitive_data(raw_error)
        logger.error(f"Unhandled exception on {request.method} {request.url.path}: {sanitized_error}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please contact the administrator."},
        )

    # Base Health Check
    @application.get("/health", tags=["Health"])
    def health_check():
        db_status = "healthy"
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
        except Exception as e:
            logger.error(f"Database health check failed: {mask_sensitive_data(str(e))}")
            db_status = "unhealthy"

        return {
            "status": "online" if db_status == "healthy" else "degraded",
            "project": settings.PROJECT_NAME,
            "engine": settings.AI_ENGINE_NAME,
            "database": db_status,
        }

    # Register API v1 routes
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


app = create_application()
