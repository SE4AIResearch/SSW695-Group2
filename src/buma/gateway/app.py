from fastapi import FastAPI

from buma.gateway.health import status as health_status
from buma.gateway.routes.webhook import router as webhook_router


def create_app() -> FastAPI:
    app = FastAPI(title="Buma Gateway", version="0.1.0")

    @app.get("/health")
    async def health() -> dict:
        return health_status()

    app.include_router(webhook_router)

    return app


app = create_app()
