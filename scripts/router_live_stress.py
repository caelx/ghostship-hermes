#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any


XML_MARKERS = ("<tool_call", "</tool_call", "<attribute", "</attribute")
PROVIDER_ENV = {
    "nvidia-build": ("NVIDIA_BUILD_API_KEY", "NVIDIA_BUILD_BASE_URL", "https://integrate.api.nvidia.com/v1"),
    "opencode-zen": ("OPENCODE_ZEN_API_KEY", "OPENCODE_ZEN_BASE_URL", "https://opencode.ai/zen/v1"),
    "openrouter": ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    "zenmux": ("ZENMUX_API_KEY", "ZENMUX_BASE_URL", "https://zenmux.ai/api/v1"),
    "electron-hub": ("ELECTRON_HUB_API_KEY", "ELECTRON_HUB_BASE_URL", "https://api.electronhub.ai/v1"),
    "opencode-go": ("OPENCODE_GO_API_KEY", "OPENCODE_GO_BASE_URL", "https://opencode.ai/zen/go/v1"),
}


@dataclass
class Result:
    name: str
    ok: bool
    status: int | None = None
    provider: str | None = None
    model: str | None = None
    error: str | None = None
    elapsed_ms: float | None = None
    first_byte_ms: float | None = None


class RouterClient:
    def __init__(self, base_url: str, api_key: str | None, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, str], bytes]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.status, {key.lower(): value for key, value in response.headers.items()}, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, {key.lower(): value for key, value in exc.headers.items()}, exc.read()
        except TimeoutError as exc:
            return 599, {}, f"request timed out after {self.timeout}s: {exc}".encode()
        except OSError as exc:
            return 598, {}, f"request transport error: {type(exc).__name__}: {exc}".encode()

    def json(self, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, str], Any]:
        status, headers, raw = self.request(method, path, body)
        try:
            return status, headers, json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            return status, headers, raw.decode(errors="replace")


def has_xml_tool_call(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower() if not isinstance(value, str) else value.lower()
    return any(marker in text for marker in XML_MARKERS)


def tool_schema() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "skill_view",
                "description": "View a named Hermes skill.",
                "parameters": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                    "additionalProperties": False,
                },
            },
        }
    ]


def simple_chat(model: str, content: str, *, stream: bool = False) -> dict[str, Any]:
    return {
        "model": model,
        "stream": stream,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 96,
    }


def sanitized_shape(payload: dict[str, Any]) -> dict[str, Any]:
    shaped: dict[str, Any] = {}
    for key, value in payload.items():
        if key == "messages" and isinstance(value, list):
            shaped["messages"] = [
                {
                    "role": item.get("role"),
                    "content_type": type(item.get("content")).__name__,
                    "has_tool_calls": isinstance(item.get("tool_calls"), list),
                    "has_tool_call_id": bool(item.get("tool_call_id")),
                    "has_reasoning_content": "reasoning_content" in item,
                }
                for item in value
                if isinstance(item, dict)
            ]
        elif key == "tools" and isinstance(value, list):
            shaped["tools"] = [item.get("function", {}).get("name") for item in value if isinstance(item, dict)]
        else:
            shaped[key] = value
    return shaped


def provider_env(provider: str) -> tuple[str | None, str | None]:
    spec = PROVIDER_ENV.get(provider)
    if spec is None:
        return None, None
    key_name, base_name, default_base = spec
    key = os.environ.get(key_name)
    if provider == "opencode-zen":
        key = key or os.environ.get("OPENCODE_API_KEY")
    if provider == "nvidia-build":
        key = key or os.environ.get("NVIDIA_API_KEY")
    base_url = os.environ.get(base_name)
    if provider == "opencode-zen":
        base_url = base_url or os.environ.get("OPENCODE_BASE_URL")
    return key, (base_url or default_base).rstrip("/")


def direct_provider_case(provider: str, backend_model: str, *, timeout: float, stream: bool) -> Result:
    key, base_url = provider_env(provider)
    name = f"direct-{provider} {'stream' if stream else 'chat'} {backend_model}"
    if not key or not base_url:
        return Result(name, False, provider=provider, model=backend_model, error="provider env is not configured")
    body = {
        "model": backend_model,
        "messages": [{"role": "user", "content": "Reply with the word ok."}],
        "max_tokens": 16,
        "stream": stream,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "ghostship-hermes-router",
        "x-api-key": key,
    }
    request = urllib.request.Request(f"{base_url}/chat/completions", data=json.dumps(body).encode(), headers=headers, method="POST")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            headers_ms = round((time.monotonic() - started) * 1000, 2)
            if stream:
                first_line = b""
                while not first_line:
                    first_line = response.readline()
                    if not first_line:
                        break
                first_ms = round((time.monotonic() - started) * 1000, 2)
                text = first_line.decode(errors="replace")
                ok = response.status < 400 and bool(first_line)
                return Result(name, ok, status=response.status, provider=provider, model=backend_model, elapsed_ms=headers_ms, first_byte_ms=first_ms, error=None if ok else f"empty first stream line shape={sanitized_shape(body)!r} body={text[:500]!r}")
            raw = response.read(1000)
            elapsed = round((time.monotonic() - started) * 1000, 2)
            ok = response.status < 400 and bool(raw)
            return Result(name, ok, status=response.status, provider=provider, model=backend_model, elapsed_ms=elapsed, first_byte_ms=headers_ms, error=None if ok else f"empty body shape={sanitized_shape(body)!r}")
    except urllib.error.HTTPError as exc:
        elapsed = round((time.monotonic() - started) * 1000, 2)
        text = exc.read(1000).decode(errors="replace")
        return Result(name, False, status=exc.code, provider=provider, model=backend_model, elapsed_ms=elapsed, error=f"upstream HTTP body={text[:500]!r} shape={sanitized_shape(body)!r}")
    except Exception as exc:
        elapsed = round((time.monotonic() - started) * 1000, 2)
        return Result(name, False, provider=provider, model=backend_model, elapsed_ms=elapsed, error=f"{type(exc).__name__}: {exc} shape={sanitized_shape(body)!r}")


def run_json_case(client: RouterClient, name: str, path: str, payload: dict[str, Any]) -> Result:
    started = time.monotonic()
    status, headers, body = client.json("POST", path, payload)
    elapsed = round((time.monotonic() - started) * 1000, 2)
    provider = headers.get("x-ghostship-router-backend-provider")
    backend = headers.get("x-ghostship-router-backend-model")
    if status >= 500:
        return Result(name, False, status=status, provider=provider, model=backend, elapsed_ms=elapsed, error=f"server error body={body!r}")
    if status >= 400:
        return Result(name, False, status=status, provider=provider, model=backend, elapsed_ms=elapsed, error=f"client error body={body!r}")
    if has_xml_tool_call(body):
        return Result(name, False, status=status, provider=provider, model=backend, elapsed_ms=elapsed, error="raw XML tool call leaked")
    return Result(name, True, status=status, provider=provider, model=backend, elapsed_ms=elapsed)


def run_stream_case(client: RouterClient, name: str, path: str, payload: dict[str, Any]) -> Result:
    payload = {**payload, "stream": True}
    status, headers, raw = client.request("POST", path, payload)
    provider = headers.get("x-ghostship-router-backend-provider")
    backend = headers.get("x-ghostship-router-backend-model")
    text = raw.decode(errors="replace")
    if status >= 500:
        return Result(name, False, status=status, provider=provider, model=backend, error=f"server error body={text[:500]!r}")
    if status >= 400:
        return Result(name, False, status=status, provider=provider, model=backend, error=f"client error body={text[:500]!r}")
    if "data: [DONE]" not in text and "response.completed" not in text:
        return Result(name, False, status=status, provider=provider, model=backend, error="stream did not complete")
    if has_xml_tool_call(text):
        return Result(name, False, status=status, provider=provider, model=backend, error="raw XML tool call leaked")
    return Result(name, True, status=status, provider=provider, model=backend)


def print_result(result: Result) -> None:
    status = result.status if result.status is not None else "-"
    route = f"{result.provider or '-'} / {result.model or '-'}"
    timings = []
    if result.elapsed_ms is not None:
        timings.append(f"elapsed={result.elapsed_ms}ms")
    if result.first_byte_ms is not None:
        timings.append(f"first_byte={result.first_byte_ms}ms")
    suffix = f" ({', '.join(timings)})" if timings else ""
    outcome = "PASS" if result.ok else "FAIL"
    print(f"{outcome} {status} {result.name}{suffix} [{route}]")
    if result.error:
        print(f"  {result.error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Live stress test for ghostship-hermes-router.")
    parser.add_argument("--base-url", default=os.environ.get("GHOSTSHIP_ROUTER_STRESS_URL", "http://127.0.0.1:8788"))
    parser.add_argument("--api-key", default=os.environ.get("_GHOSTSHIP_ROUTER_API_KEY") or os.environ.get("GHOSTSHIP_ROUTER_API_KEY"))
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("GHOSTSHIP_ROUTER_STRESS_TIMEOUT", "90")))
    parser.add_argument("--rpm-burst", type=int, default=int(os.environ.get("GHOSTSHIP_ROUTER_STRESS_RPM_BURST", "16")))
    parser.add_argument("--models", default=os.environ.get("GHOSTSHIP_ROUTER_STRESS_MODELS", ""))
    parser.add_argument("--direct-provider-probes", action="store_true", default=os.environ.get("GHOSTSHIP_ROUTER_STRESS_DIRECT_PROVIDERS", "").lower() in {"1", "true", "yes"})
    args = parser.parse_args()

    client = RouterClient(args.base_url, args.api_key, args.timeout)
    results: list[Result] = []

    for name, path in (("readyz", "/readyz"), ("models", "/v1/models"), ("debug-summary", "/debug/summary"), ("metrics", "/metrics")):
        status, _, body = client.request("GET", path)
        ok = status < 500 and bool(body)
        results.append(Result(name, ok, status=status, error=None if ok else body.decode(errors="replace")[:500]))

    status, _, models_body = client.json("GET", "/v1/models")
    if status != 200 or not isinstance(models_body, dict):
        results.append(Result("load-models", False, status=status, error=f"could not load models: {models_body!r}"))
        for result in results:
            print_result(result)
        return 1

    models = [item["id"] for item in models_body.get("data", []) if isinstance(item, dict) and item.get("id")]
    requested_models = [item.strip() for item in args.models.split(",") if item.strip()]
    if requested_models:
        models = [model for model in models if model in requested_models]
    if not models:
        results.append(Result("model-catalog-nonempty", False, status=200, error="/v1/models returned no served models"))

    for model in models:
        status, _, route_body = client.json("GET", f"/debug/routes/{model}")
        results.append(Result(f"debug-routes {model}", status == 200, status=status))
        route_entries: list[dict[str, Any]] = []
        if isinstance(route_body, dict):
            for key in ("candidates", "skipped"):
                values = route_body.get(key)
                if isinstance(values, list):
                    route_entries.extend(item for item in values if isinstance(item, dict))
        if args.direct_provider_probes:
            rankings_status, _, rankings_body = client.json("GET", f"/debug/rankings/{model}")
            if rankings_status == 200 and isinstance(rankings_body, dict):
                for provider_item in rankings_body.get("providers", []):
                    if not isinstance(provider_item, dict):
                        continue
                    provider_name = str(provider_item.get("provider_name") or "")
                    for seeded_item in provider_item.get("seeded", []):
                        if isinstance(seeded_item, dict) and seeded_item.get("backend_model"):
                            route_entries.append(
                                {
                                    "provider_name": provider_name,
                                    "backend_model": seeded_item["backend_model"],
                                }
                            )
        if args.direct_provider_probes:
            seen_direct: set[tuple[str, str]] = set()
            for item in route_entries:
                provider = str(item.get("provider_name") or "")
                backend_model = str(item.get("backend_model") or "")
                if not provider or not backend_model or (provider, backend_model) in seen_direct:
                    continue
                seen_direct.add((provider, backend_model))
                results.append(direct_provider_case(provider, backend_model, timeout=args.timeout, stream=False))
                results.append(direct_provider_case(provider, backend_model, timeout=args.timeout, stream=True))
        results.append(run_json_case(client, f"chat {model}", "/v1/chat/completions", simple_chat(model, "Reply with the word ok.")))
        results.append(run_stream_case(client, f"chat-stream {model}", "/v1/chat/completions", simple_chat(model, "Reply with the word ok.")))
        tool_payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Call skill_view for ghostship-media-services-health."}],
            "tools": tool_schema(),
            "tool_choice": "auto",
            "max_tokens": 128,
        }
        results.append(run_json_case(client, f"tool-call {model}", "/v1/chat/completions", tool_payload))
        results.append(run_stream_case(client, f"tool-stream {model}", "/v1/chat/completions", tool_payload))
        assistant_tool_message: dict[str, Any] = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_stress_1",
                    "type": "function",
                    "function": {"name": "skill_view", "arguments": "{\"name\":\"ghostship-media-services-health\"}"},
                }
            ],
        }
        if model.startswith("deepseek-"):
            assistant_tool_message["reasoning_content"] = "The prior assistant turn selected the skill_view function."
        history_payload = {
            "model": model,
            "messages": [
                assistant_tool_message,
                {"role": "tool", "tool_call_id": "call_stress_1", "content": "{\"status\":\"ok\"}"},
                {"role": "user", "content": "Summarize the tool output in one short sentence."},
            ],
            "tools": tool_schema(),
            "max_tokens": 128,
        }
        results.append(run_json_case(client, f"tool-history {model}", "/v1/chat/completions", history_payload))
        responses_payload = {"model": model, "input": "Reply with the word ok.", "max_output_tokens": 96}
        results.append(run_json_case(client, f"responses {model}", "/v1/responses", responses_payload))
        results.append(run_stream_case(client, f"responses-stream {model}", "/v1/responses", responses_payload))

    if models and args.rpm_burst > 0:
        burst_model = models[0]
        with ThreadPoolExecutor(max_workers=min(args.rpm_burst, 20)) as executor:
            futures = [
                executor.submit(
                    run_json_case,
                    client,
                    f"rpm-burst-{index}",
                    "/v1/chat/completions",
                    simple_chat(burst_model, f"RPM burst probe {index}. Reply ok."),
                )
                for index in range(args.rpm_burst)
            ]
            for future in as_completed(futures):
                results.append(future.result())

    for result in results:
        print_result(result)
    providers = sorted({result.provider for result in results if result.provider})
    print(f"Providers observed: {', '.join(providers) if providers else 'none'}")
    failures = [result for result in results if not result.ok]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
