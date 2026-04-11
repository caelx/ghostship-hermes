"""Hermes HUD Web UI backend."""

from __future__ import annotations

import argparse
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import (
    agents,
    cache,
    console,
    corrections,
    cron,
    dashboard,
    health,
    memory,
    patterns,
    profiles,
    projects,
    sessions,
    skills,
    snapshots,
    state,
    timeline,
    token_costs,
)
from .console import ensure_state_dir, proxy_terminal_http, proxy_terminal_websocket
from .file_watcher import start_watcher, stop_watcher
from .websocket_manager import ws_manager

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).parent / 'static'
DASHBOARD_HOST = os.environ.get('GHOSTSHIP_DASHBOARD_HOST', '0.0.0.0')
DASHBOARD_PORT = int(os.environ.get('GHOSTSHIP_DASHBOARD_PORT', '7681'))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    hermes_dir = os.environ.get('HERMES_HOME') or os.path.expanduser('~/.hermes')
    ensure_state_dir()
    watcher_enabled = os.environ.get('GHOSTSHIP_HUD_DISABLE_WATCHER') != '1'
    if watcher_enabled:
        await start_watcher(hermes_dir)
        logger.info('Hermes HUD started, watching %s', hermes_dir)
    else:
        logger.info('Hermes HUD started with watcher disabled')
    yield
    if watcher_enabled:
        await stop_watcher()
    logger.info('Hermes HUD stopped')


app = FastAPI(title='Hermes HUD', version='0.1.0', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == 'ping':
                await websocket.send_text('pong')
    except Exception:
        pass
    finally:
        await ws_manager.disconnect(websocket)


@app.get('/healthz')
def healthz() -> dict[str, bool]:
    return {'ok': True}


app.include_router(state.router, prefix='/api')
app.include_router(memory.router, prefix='/api')
app.include_router(sessions.router, prefix='/api')
app.include_router(skills.router, prefix='/api')
app.include_router(cron.router, prefix='/api')
app.include_router(projects.router, prefix='/api')
app.include_router(health.router, prefix='/api')
app.include_router(profiles.router, prefix='/api')
app.include_router(patterns.router, prefix='/api')
app.include_router(corrections.router, prefix='/api')
app.include_router(agents.router, prefix='/api')
app.include_router(timeline.router, prefix='/api')
app.include_router(snapshots.router, prefix='/api')
app.include_router(dashboard.router, prefix='/api')
app.include_router(token_costs.router, prefix='/api')
app.include_router(cache.router, prefix='/api')
app.include_router(console.router, prefix='/api')
app.add_api_route(
    '/terminals/{session_id}/{path:path}',
    proxy_terminal_http,
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'PATCH', 'TRACE'],
)
app.add_api_websocket_route('/terminals/{session_id}/{path:path}', proxy_terminal_websocket)

if STATIC_DIR.exists():
    app.mount('/', StaticFiles(directory=str(STATIC_DIR), html=True), name='static')


def cli() -> None:
    parser = argparse.ArgumentParser(description='Hermes HUD Web UI')
    parser.add_argument('--port', type=int, default=DASHBOARD_PORT, help='Port (default: 7681)')
    parser.add_argument('--host', default=DASHBOARD_HOST, help='Host (default: 0.0.0.0)')
    parser.add_argument('--dev', action='store_true', help='Development mode (auto-reload)')
    parser.add_argument('--hermes-dir', default=None, help='Hermes data directory (default: ~/.hermes)')
    args = parser.parse_args()
    if args.hermes_dir:
        os.environ['HERMES_HOME'] = args.hermes_dir
    import uvicorn
    uvicorn.run('hermes_dashboard.app:app', host=args.host, port=args.port, reload=args.dev)


if __name__ == '__main__':
    cli()
