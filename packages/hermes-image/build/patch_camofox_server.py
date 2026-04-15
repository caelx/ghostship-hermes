from __future__ import annotations

import sys
from pathlib import Path


OLD = """  res.json({ \n    ok: true, \n    engine: 'camoufox',\n    browserConnected: running,\n    browserRunning: running,\n    activeTabs: getTotalTabCount(),\n    activeSessions: sessions.size,\n    consecutiveFailures: healthState.consecutiveNavFailures,\n    ...(FLY_MACHINE_ID ? { machineId: FLY_MACHINE_ID } : {}),\n  });\n});\n"""

NEW = """  const vncPort = parseInt(process.env.GHOSTSHIP_CAMOFOX_WEB_PORT || '', 10);\n  res.json({ \n    ok: true, \n    engine: 'camoufox',\n    browserConnected: running,\n    browserRunning: running,\n    activeTabs: getTotalTabCount(),\n    activeSessions: sessions.size,\n    consecutiveFailures: healthState.consecutiveNavFailures,\n    ...(Number.isInteger(vncPort) && vncPort > 0 ? { vncPort } : {}),\n    ...(FLY_MACHINE_ID ? { machineId: FLY_MACHINE_ID } : {}),\n  });\n});\n"""


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_camofox_server.py <server.js>")

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    if "GHOSTSHIP_CAMOFOX_WEB_PORT" in text:
        return
    if OLD not in text:
        raise SystemExit(f"expected health block not found in {path}")
    path.write_text(text.replace(OLD, NEW), encoding="utf-8")


if __name__ == "__main__":
    main()
