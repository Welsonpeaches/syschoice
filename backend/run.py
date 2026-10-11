"""Development entrypoint: python run.py

Config comes from environment variables. Anything you would rather keep in a
file can go in ``backend/.env`` (see ``.env.example``); real environment
variables always win over the file.
"""

import os
from pathlib import Path


def load_env_file(path):
    """Minimal .env reader so no extra dependency is needed."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        # Strip the quotes people habitually add around secrets.
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# Must run before `app` is imported: Config reads the environment at import time.
load_env_file(Path(__file__).with_name(".env"))

from app import create_app  # noqa: E402  (import order matters, see above)

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    # '::' accepts IPv4 and IPv6 on Linux; override with SYSCHOICE_HOST.
    host = os.environ.get("SYSCHOICE_HOST", "::")
    app.run(host=host, port=port, debug=True)
