from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from .config import RouterConfig
from .models import ChatCompletionRequest, HealthResponse
from .service import RouterService, RouterServiceError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hermes_router")


def create_app(*, config: RouterConfig | None = None, service: RouterService | None = None) -> FastAPI:
    resolved_config = config or RouterConfig.from_env()
    resolved_service = service or RouterService(resolved_config)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await asyncio.to_thread(resolved_service.refresh_inventory, reason="startup")

        async def refresh_loop() -> None:
            while True:
                await asyncio.sleep(resolved_config.refresh_interval_seconds)
                await asyncio.to_thread(resolved_service.refresh_inventory, reason="scheduled")

        refresh_task = asyncio.create_task(refresh_loop())
        try:
            yield
        finally:
            refresh_task.cancel()
            try:
                await refresh_task
            except asyncio.CancelledError:
                pass

    app = FastAPI(title="ghostship-hermes-router", lifespan=lifespan)

    @app.get("/healthz")
    def healthz() -> HealthResponse:
        return HealthResponse(ok=True)

    @app.get("/readyz")
    def readyz(response: Response):
        payload = resolved_service.readiness()
        if not payload.ok:
            response.status_code = 503
        return payload

    @app.get("/v1/models")
    def list_models():
        try:
            return resolved_service.list_models()
        except RouterServiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @app.get("/debug/state")
    def debug_state():
        return resolved_service.debug_state()

    @app.get("/debug/events")
    def debug_events():
        return resolved_service.debug_events()

    @app.get("/debug/providers")
    def debug_providers():
        return resolved_service.debug_providers()

    @app.get("/debug/rankings/{alias}")
    def debug_rankings(alias: str):
        try:
            return resolved_service.debug_rankings(alias)
        except RouterServiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @app.get("/debug/routes/{alias}")
    def debug_routes(alias: str):
        return {"alias": alias, "candidates": resolved_service.preview_routes(alias)}

    @app.get("/debug/models/{provider_name}/{backend_model:path}")
    def debug_model(provider_name: str, backend_model: str):
        try:
            return resolved_service.debug_model(provider_name, backend_model)
        except RouterServiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @app.get("/metrics")
    def metrics():
        return PlainTextResponse(resolved_service.metrics_text(), media_type="text/plain; version=0.0.4; charset=utf-8")

    @app.post("/v1/chat/completions")
    def chat_completions(request: ChatCompletionRequest):
        try:
            payload, headers = resolved_service.chat_completions(request)
        except RouterServiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
        return JSONResponse(payload, headers=headers)

    return app


def main() -> None:
    config = RouterConfig.from_env()
    uvicorn.run(create_app(config=config), host=config.host, port=config.port, log_level=config.log_level)


if __name__ == "__main__":
    main()
