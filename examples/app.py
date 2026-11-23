"""A tiny web server configured with tidyconf.

Run it from the repo root (after `pip install -e .`):

    python examples/app.py
    HELLO_SERVER__PORT=9000 HELLO_GREETING="Hi there" python examples/app.py

Then open http://127.0.0.1:8000 (or the port you chose).
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from tidyconf import Config, optional

HERE = Path(__file__).resolve().parent

config = Config.load(
    HERE / "config.toml",  # defaults
    optional(HERE / "config.local.toml"),  # per-machine overrides, if present
    env_prefix="HELLO",  # e.g. HELLO_SERVER__PORT=9000
)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body: dict[str, object] = {"message": config["greeting"]}
        if config["debug"]:
            body["config"] = config.to_dict()
        payload = json.dumps(body, indent=2).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    host, port = config["server.host"], config["server.port"]
    print(f"Serving on http://{host}:{port} (Ctrl+C to stop)")
    HTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
