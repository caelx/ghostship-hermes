from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import RouterConfig
from .models import ApiHealthResponse, ChatCompletionRequest, HealthResponse
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

    if resolved_config.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_config.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def require_api_key(request: Request) -> None:
        if resolved_config.api_key is None:
            return
        auth_header = request.headers.get("authorization")
        expected = f"Bearer {resolved_config.api_key}"
        if auth_header == expected:
            return
        raise HTTPException(status_code=401, detail="Unauthorized")

    @app.get("/health")
    def health() -> ApiHealthResponse:
        return ApiHealthResponse(status="ok")

    @app.get("/v1/health")
    def api_health() -> ApiHealthResponse:
        return ApiHealthResponse(status="ok")

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
    def list_models(request: Request):
        require_api_key(request)
        try:
            return resolved_service.list_models()
        except RouterServiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @app.get("/debug/state")
    def debug_state(request: Request):
        require_api_key(request)
        return resolved_service.debug_state()

    @app.get("/debug/events")
    def debug_events(request: Request):
        require_api_key(request)
        return resolved_service.debug_events()

    @app.get("/debug/routes/{alias}")
    def debug_routes(alias: str, request: Request):
        require_api_key(request)
        return {"alias": alias, "candidates": resolved_service.preview_routes(alias)}

    @app.post("/v1/chat/completions")
    def chat_completions(request: ChatCompletionRequest, raw_request: Request):
        require_api_key(raw_request)
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
