from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.logging import setup_logging, RequestTracingMiddleware
from app.api.uploads import router as uploads_router
from app.api.reports import router as reports_router
from app.api.issues import router as issues_router
from app.api.auth import router as auth_router
from app.api.map import router as map_router
from app.api.lookup import router as lookup_router
from app.api.admin_jurisdictions import router as admin_jurisdictions_router, override_router
from app.api.admin_moderation import router as admin_moderation_router
from app.api.admin_issues import router as admin_issues_router
from app.api.admin_authorities import router as admin_authorities_router, chain_router as admin_chain_router
from app.api.admin_analytics import router as admin_analytics_router
from app.api.admin_audit import router as admin_audit_router
from app.api.admin_users import router as admin_users_router
from app.api.hotspots import router as hotspots_router
from app.api.search import router as search_router
from app.api.areas import router as areas_router
from app.api.stats import router as stats_router
from app.api.subscriptions import router as subscriptions_router
from app.api.authorities_public import router as authorities_public_router

settings = get_settings()
setup_logging(debug=settings.DEBUG)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure MinIO bucket exists
    from app.services.storage import ensure_bucket_exists
    try:
        ensure_bucket_exists()
    except Exception:
        pass  # MinIO may not be running in tests
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracing
app.add_middleware(RequestTracingMiddleware)

# Register routes
app.include_router(uploads_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)
app.include_router(issues_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(map_router, prefix=settings.API_V1_PREFIX)
app.include_router(lookup_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_jurisdictions_router, prefix=settings.API_V1_PREFIX)
app.include_router(override_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_moderation_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_issues_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_authorities_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_chain_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_audit_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_users_router, prefix=settings.API_V1_PREFIX)
app.include_router(hotspots_router, prefix=settings.API_V1_PREFIX)
app.include_router(search_router, prefix=settings.API_V1_PREFIX)
app.include_router(areas_router, prefix=settings.API_V1_PREFIX)
app.include_router(stats_router, prefix=settings.API_V1_PREFIX)
app.include_router(subscriptions_router, prefix=settings.API_V1_PREFIX)
app.include_router(authorities_public_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
