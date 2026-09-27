"""Run the dashboard with `python -m d_brain.dashboard`.

Binds to localhost only — this is a local-first tool. Reach it over an
SSH tunnel (see deploy/secondbrain-dashboard.service).
"""

import os

import uvicorn

HOST = "127.0.0.1"
PORT = int(os.environ.get("DASHBOARD_PORT", "8765"))


def main() -> None:
    uvicorn.run("d_brain.dashboard.app:app", host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
