"""
FastAPI application entry point for GoodEats Recipe PWA.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.config.database import create_tables
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ConflictError,
    RateLimitError
)

# Import routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.recipes import router as recipes_router
from app.api.tags import router as tags_router
from app.api.votes import router as votes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    """
    # Startup
    if settings.is_development:
        # Create tables in development mode
        await create_tables()
    
    yield
    
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A Progressive Web Application for recipe management with social features",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "type": "authentication_error"
        },
        headers=exc.headers
    )


@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "type": "authorization_error"
        }
    )


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "type": "not_found_error"
        }
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "type": "validation_error"
        }
    )


@app.exception_handler(ConflictError)
async def conflict_exception_handler(request: Request, exc: ConflictError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "type": "conflict_error"
        }
    )


@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "type": "rate_limit_error"
        }
    )


# Include routers
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

app.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)

app.include_router(
    recipes_router,
    prefix="/recipes",
    tags=["recipes"]
)

app.include_router(
    tags_router,
    prefix="/tags",
    tags=["tags"]
)

app.include_router(
    votes_router,
    prefix="/votes",
    tags=["votes"]
)


# Root endpoints
@app.get("/")
async def root():
    """
    API root endpoint.
    """
    return {
        "message": "Welcome to GoodEats Recipe PWA API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "goodEats-api",
        "version": settings.APP_VERSION
    }


# Development utilities
if settings.DEBUG:
    
    @app.get("/debug/info")
    async def debug_info():
        """
        Debug information endpoint.
        """
        return {
            "debug": settings.DEBUG,
            "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "***",
            "cors_origins": settings.cors_origins_list,
            "environment": "development" if settings.is_development else "production"
        }