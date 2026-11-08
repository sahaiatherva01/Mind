"""
Mind FastAPI Application Entrypoint
Base Path: /api/v1
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.db import engine, Base
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import get_logger

# Domain Routers
from backend.app.identity.router import auth_router, user_router
from backend.app.tenancy.router import router as tenancy_router
from backend.app.academics.router import (
    classes_router,
    subjects_router,
    assignments_router,
    enrollments_router,
    curriculum_router,
    academics_router,
)
from backend.app.audit.router import router as audit_router

logger = get_logger("mind.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Mind backend application...")
    # In development / testing, create tables if they do not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down Mind backend application...")
    await engine.dispose()


app = FastAPI(
    title=f"{settings.PRODUCT_DISPLAY_NAME} API",
    description="Intelligence for Better Learning — AI-Powered Academic Assessment & Learning Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
register_exception_handlers(app)

# Mount API v1 Routers
api_v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(user_router, prefix=api_v1_prefix)
app.include_router(tenancy_router, prefix=api_v1_prefix)
app.include_router(classes_router, prefix=api_v1_prefix)
app.include_router(subjects_router, prefix=api_v1_prefix)
app.include_router(assignments_router, prefix=api_v1_prefix)
app.include_router(enrollments_router, prefix=api_v1_prefix)
app.include_router(curriculum_router, prefix=api_v1_prefix)
app.include_router(academics_router, prefix=api_v1_prefix)
app.include_router(audit_router, prefix=api_v1_prefix)


@app.get("/health", tags=["Health"])
@app.get(f"{api_v1_prefix}/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.PRODUCT_DISPLAY_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }
