"""Unit Tests for Bottle Micro-Web Framework Application and Endpoints."""

import io
import json
import unittest
from web_app import app


def wsgi_request(app_instance, path: str, method: str = "GET", body: dict = None):
    """Invokes Bottle WSGI application directly without opening network sockets."""
    body_bytes = json.dumps(body).encode("utf-8") if body else b""
    environ = {
        "PATH_INFO": path,
        "REQUEST_METHOD": method,
        "wsgi.input": io.BytesIO(body_bytes),
        "CONTENT_LENGTH": str(len(body_bytes)),
        "CONTENT_TYPE": "application/json" if body else "",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8080",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http",
        "wsgi.errors": io.StringIO(),
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": True,
    }
    status_capture = []
    headers_capture = []

    def start_response(status, headers, exc_info=None):
        status_capture.append(status)
        headers_capture.extend(headers)

    body_chunks = app_instance(environ, start_response)
    return status_capture[0], headers_capture, b"".join(body_chunks).decode("utf-8")


class TestBottleWebApp(unittest.TestCase):
    """Tests Bottle REST API endpoints and dashboard serving."""

    def test_get_status_endpoint(self) -> None:
        status, headers, body = wsgi_request(app, "/api/v1/status", "GET")
        self.assertTrue(status.startswith("200"))
        data = json.loads(body)
        self.assertEqual(data["status"], "HEALTHY")
        self.assertIn("Bottle", data["frameworks"]["web_framework"])
        self.assertIn("Snowflake", data["frameworks"]["data_warehouse"])

    def test_get_dashboard_html(self) -> None:
        status, headers, body = wsgi_request(app, "/", "GET")
        self.assertTrue(status.startswith("200"))
        self.assertIn("Bank Transaction Anomaly Flagger", body)
        self.assertIn("Bottle", body)

    def test_screen_transaction_endpoint(self) -> None:
        payload = {
            "sender_id": "ACC_ALICE",
            "receiver_id": "ACC_BOB",
            "amount": 50.0,
            "channel": "MOBILE_APP",
        }
        status, headers, body = wsgi_request(app, "/api/v1/screen", "POST", payload)
        self.assertTrue(status.startswith("200"))
        data = json.loads(body)

        # Must have a generated 64-bit Snowflake ID
        self.assertTrue(data["snowflake_txn_id"].startswith("TXN_SNOW_"))
        self.assertIn("snowflake_metadata", data)
        self.assertEqual(data["screening_decision"]["action"], "APPROVE")
        self.assertEqual(data["snowflake_warehouse_status"], "COMMITTED_TO_FACT_TRANSACTIONS")

    def test_get_transactions_endpoint(self) -> None:
        status, headers, body = wsgi_request(app, "/api/v1/transactions", "GET")
        self.assertTrue(status.startswith("200"))
        data = json.loads(body)
        self.assertIn("records", data)
        self.assertIsInstance(data["records"], list)

    def test_serve_static_files(self) -> None:
        status_css, _, body_css = wsgi_request(app, "/static/css/styles.css", "GET")
        self.assertTrue(status_css.startswith("200"))
        self.assertIn("--bg-main", body_css)

        status_js, _, body_js = wsgi_request(app, "/static/js/app.js", "GET")
        self.assertTrue(status_js.startswith("200"))
        self.assertIn("handleScreenTransaction", body_js)


if __name__ == "__main__":
    unittest.main()
