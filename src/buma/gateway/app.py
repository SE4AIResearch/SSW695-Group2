from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from buma.core.config import get_settings
from buma.gateway.health import status as health_status
from buma.gateway.routes.config import router as config_router
from buma.gateway.routes.dev import router as dev_router
from buma.gateway.routes.observability import router as observability_router
from buma.gateway.routes.webhook import router as webhook_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Buma Gateway", version="0.1.0")

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return health_status()

    app.include_router(webhook_router)
    app.include_router(config_router)
    app.include_router(observability_router)
    app.include_router(dev_router)

    return app


app = create_app()
