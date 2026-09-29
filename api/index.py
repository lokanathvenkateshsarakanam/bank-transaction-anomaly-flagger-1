"""Universal Vercel Serverless Function Adapter for Bank Transaction Anomaly Flagger.

Compatible with:
1. Native Vercel BaseHTTPRequestHandler serverless contract.
2. WSGI (Bottle) application bridge.
"""

from http.server import BaseHTTPRequestHandler
from io import BytesIO
import os
import sys
import urllib.parse

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from web_app import app


class handler(BaseHTTPRequestHandler):
    """Vercel serverless request handler adapting HTTP to Bottle WSGI."""

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_PUT(self) -> None:
        self._dispatch("PUT")

    def do_DELETE(self) -> None:
        self._dispatch("DELETE")

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _dispatch(self, method: str) -> None:
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": parsed.path or "/",
            "QUERY_STRING": parsed.query or "",
            "SERVER_NAME": "vercel",
            "SERVER_PORT": "443",
            "SERVER_PROTOCOL": getattr(self, "request_version", "HTTP/1.1"),
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "https",
            "wsgi.input": BytesIO(body),
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": True,
        }

        # Propagate headers to WSGI environ
        if hasattr(self, "headers") and self.headers:
            for k, v in self.headers.items():
                k_upper = k.upper().replace("-", "_")
                if k_upper in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                    environ[k_upper] = v
                else:
                    environ["HTTP_" + k_upper] = v

        status_code = 200
        response_headers = []

        def start_response(status, headers, exc_info=None):
            nonlocal status_code, response_headers
            try:
                status_code = int(status.split(" ")[0])
            except Exception:
                status_code = 200
            response_headers = headers

        try:
            result = app(environ, start_response)
            self.send_response(status_code)
            for name, value in response_headers:
                self.send_header(name, value)
            self.end_headers()

            for chunk in result:
                if isinstance(chunk, str):
                    self.wfile.write(chunk.encode("utf-8"))
                else:
                    self.wfile.write(chunk)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err_payload = '{"error": "Internal Server Error", "details": "' + str(e).replace('"', '\\"') + '"}'
            self.wfile.write(err_payload.encode("utf-8"))
