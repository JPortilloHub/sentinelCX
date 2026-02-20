"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from sentinelcx.api.routes import dashboard, dashboard_sse, evaluation, health, tickets
from sentinelcx.api.webhooks import chatwoot
from sentinelcx.config import Settings
from sentinelcx.dashboard.log_monitor import get_log_monitor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: start MCP log monitor
    monitor = get_log_monitor()
    await monitor.start()

    yield

    # Shutdown: stop monitor
    await monitor.stop()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="sentinelCX",
        description="Enterprise Customer Support Intelligence System",
        version="0.1.0",
        lifespan=lifespan,
    )

    settings = Settings()
    app.state.settings = settings

    app.include_router(health.router, tags=["health"])
    app.include_router(tickets.router, prefix="/api/v1", tags=["tickets"])
    app.include_router(evaluation.router, prefix="/api/v1", tags=["evaluation"])
    app.include_router(chatwoot.router, prefix="/webhooks", tags=["webhooks"])
    app.include_router(dashboard.router, tags=["dashboard"])
    app.include_router(dashboard_sse.router, tags=["dashboard"])

    return app
