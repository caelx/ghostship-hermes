from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from pydantic import ValidationError

from .config import RouterConfig
from .models import ChatCompletionRequest, HealthResponse, HealthStatusResponse, ResponsesRequest
from .service import RouterService, RouterServiceError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hermes_router")


def _openai_error(message: str, *, err_type: str = "invalid_request_error", code: str | None = None) -> dict[str, object]:
    return {"error": {"message": message, "type": err_type, "code": code}}


def _authorized(request: Request, config: RouterConfig) -> bool:
    api_key = getattr(config, "api_key", None)
    if not api_key:
        return True
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and auth_header[7:].strip() == api_key:
        return True
    return False


def create_app(*, config: RouterConfig | None = None, service: RouterService | None = None) -> FastAPI:
    resolved_config = config or RouterConfig.from_env()
    resolved_service = service or RouterService(resolved_config)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async def refresh_inventory(reason: str) -> None:
            try:
                await asyncio.to_thread(resolved_service.refresh_inventory, reason=reason)
            except Exception:
                logger.exception("router inventory refresh failed: reason=%s", reason)

        async def refresh_loop() -> None:
            await refresh_inventory("startup")
            while True:
                await asyncio.sleep(resolved_config.refresh_interval_seconds)
                await refresh_inventory("scheduled")

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

    if getattr(resolved_config, "cors_origins", ()):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_config.cors_origins),
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Hermes-Session-Id"],
        )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    @app.get("/healthz")
    def healthz() -> HealthResponse:
        return HealthResponse(ok=True)

    @app.get("/health")
    @app.get("/v1/health")
    def api_health() -> HealthStatusResponse:
        return HealthStatusResponse(status="ok", platform="ghostship-hermes-router")

    @app.get("/readyz")
    def readyz(response: Response):
        payload = resolved_service.readiness()
        if not payload.ok:
            response.status_code = 503
        return payload

    @app.get("/models")
    @app.get("/v1/models")
    def list_models(request: Request):
        if not _authorized(request, resolved_config):
            return JSONResponse(_openai_error("Invalid API key", code="invalid_api_key"), status_code=401)
        try:
            return resolved_service.list_models()
        except RouterServiceError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            return JSONResponse(_openai_error(str(detail.get("message", exc.detail))), status_code=exc.status_code)

    @app.get("/debug/state")
    def debug_state():
        return resolved_service.debug_state()

    @app.get("/debug/events")
    def debug_events():
        return resolved_service.debug_events()

    @app.get("/debug/route-events")
    def debug_route_events(
        limit: int | None = None,
        alias: str | None = None,
        provider_name: str | None = None,
        backend_model: str | None = None,
        category: str | None = None,
        since: float | None = None,
        success: bool | None = None,
    ):
        return resolved_service.debug_route_events(
            limit=limit,
            alias=alias,
            provider_name=provider_name,
            backend_model=backend_model,
            category=category,
            since=since,
            success=success,
        )

    @app.get("/debug/providers")
    def debug_providers():
        return resolved_service.debug_providers()

    @app.get("/debug/summary")
    def debug_summary():
        return resolved_service.debug_summary()

    @app.get("/debug/rankings/{alias}")
    def debug_rankings(alias: str):
        try:
            return resolved_service.debug_rankings(alias)
        except RouterServiceError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            return JSONResponse(_openai_error(str(detail.get("message", exc.detail))), status_code=exc.status_code)

    @app.get("/debug/routes/{alias}")
    def debug_routes(alias: str, shape_key: str = "text"):
        try:
            return resolved_service.debug_routes(alias, shape_key=shape_key)
        except RouterServiceError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            return JSONResponse(_openai_error(str(detail.get("message", exc.detail))), status_code=exc.status_code)

    @app.get("/debug/health")
    def debug_health():
        return resolved_service.debug_health()

    @app.get("/debug/inventory/{category}")
    def debug_inventory(category: str):
        try:
            return resolved_service.debug_inventory(category)
        except RouterServiceError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            return JSONResponse(_openai_error(str(detail.get("message", exc.detail))), status_code=exc.status_code)

    @app.get("/debug/models/{provider_name}/{backend_model:path}")
    def debug_model(provider_name: str, backend_model: str):
        try:
            return resolved_service.debug_model(provider_name, backend_model)
        except RouterServiceError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            return JSONResponse(_openai_error(str(detail.get("message", exc.detail))), status_code=exc.status_code)

    @app.get("/metrics")
    def metrics():
        return PlainTextResponse(resolved_service.metrics_text(), media_type="text/plain; version=0.0.4; charset=utf-8")

    @app.post("/chat/completions")
    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        if not _authorized(request, resolved_config):
            return JSONResponse(_openai_error("Invalid API key", code="invalid_api_key"), status_code=401)
        try:
            raw_body = await request.json()
        except Exception:
            return JSONResponse(_openai_error("Invalid JSON in request body"), status_code=400)
        try:
            completion_request = ChatCompletionRequest.model_validate(raw_body)
        except ValidationError as exc:
            return JSONResponse(_openai_error(str(exc.errors()[0].get("msg", "Invalid request"))), status_code=400)
        try:
            session_id = request.headers.get("X-Hermes-Session-Id", "").strip() or None
            if completion_request.stream:
                plan = await asyncio.to_thread(
                    resolved_service.stream_chat_completions,
                    completion_request,
                    session_id=session_id,
                )
                return StreamingResponse(plan.body, media_type="text/event-stream", headers=plan.headers)
            payload, headers = await asyncio.to_thread(
                resolved_service.chat_completions,
                completion_request,
                session_id=session_id,
            )
        except RouterServiceError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            return JSONResponse(_openai_error(str(detail.get("message", exc.detail))), status_code=exc.status_code)
        return JSONResponse(payload, headers=headers)

    @app.post("/responses")
    @app.post("/v1/responses")
    async def responses_create(request: Request):
        if not _authorized(request, resolved_config):
            return JSONResponse(_openai_error("Invalid API key", code="invalid_api_key"), status_code=401)
        try:
            raw_body = await request.json()
        except Exception:
            return JSONResponse(_openai_error("Invalid JSON in request body"), status_code=400)
        try:
            responses_request = ResponsesRequest.model_validate(raw_body)
        except ValidationError as exc:
            return JSONResponse(_openai_error(str(exc.errors()[0].get("msg", "Invalid request"))), status_code=400)
        try:
            if responses_request.stream:
                plan = await asyncio.to_thread(resolved_service.responses_create_stream, responses_request)
                return StreamingResponse(plan.body, media_type="text/event-stream", headers=plan.headers)
            payload, headers = await asyncio.to_thread(resolved_service.responses_create, responses_request)
        except RouterServiceError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            return JSONResponse(_openai_error(str(detail.get("message", exc.detail))), status_code=exc.status_code)
        return JSONResponse(payload, headers=headers)

    @app.get("/responses/{response_id}")
    @app.get("/v1/responses/{response_id}")
    def responses_get(response_id: str, request: Request):
        if not _authorized(request, resolved_config):
            return JSONResponse(_openai_error("Invalid API key", code="invalid_api_key"), status_code=401)
        try:
            return resolved_service.get_response(response_id)
        except RouterServiceError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            return JSONResponse(_openai_error(str(detail.get("message", exc.detail))), status_code=exc.status_code)

    @app.delete("/responses/{response_id}")
    @app.delete("/v1/responses/{response_id}")
    def responses_delete(response_id: str, request: Request):
        if not _authorized(request, resolved_config):
            return JSONResponse(_openai_error("Invalid API key", code="invalid_api_key"), status_code=401)
        try:
            return resolved_service.delete_response(response_id)
        except RouterServiceError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            return JSONResponse(_openai_error(str(detail.get("message", exc.detail))), status_code=exc.status_code)

    return app


def main() -> None:
    config = RouterConfig.from_env()
    uvicorn.run(create_app(config=config), host=config.host, port=config.port, log_level=config.log_level)


if __name__ == "__main__":
    main()
