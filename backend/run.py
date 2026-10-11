"""Development entrypoint: python run.py"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    # '::' accepts IPv4 and IPv6 on Linux; override with SYSCHOICE_HOST.
    host = os.environ.get("SYSCHOICE_HOST", "::")
    app.run(host=host, port=port, debug=True)
