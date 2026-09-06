"""
Uvicorn entrypoint for the rulial-markets backend.

    python backend/main.py                 # :8000, reload off
    RULIAL_RELOAD=1 python backend/main.py # :8000, autoreload for dev
    uvicorn main:app --port 8000           # from inside backend/

Port 8000 is frozen by CONTRACT.md section 6 (the frontend dev server on :3000
proxies /api/* here). Override only for local experiments via PORT env.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `rulial` importable no matter where this is launched from.
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from rulial.api import app  # noqa: E402  (path setup must happen first)

__all__ = ["app"]


def main() -> None:
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    reload_on = os.environ.get("RULIAL_RELOAD", "").lower() in ("1", "true", "yes")
    if reload_on:
        uvicorn.run("rulial.api:app", host=host, port=port, reload=True,
                    reload_dirs=[str(BACKEND_DIR)], log_level="info")
    else:
        uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
