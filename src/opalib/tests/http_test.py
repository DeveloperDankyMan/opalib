"""HTTP tests for opalib.http."""

import http.server
import importlib.util
import threading
import time
import unittest
from pathlib import Path


class TestHttp(unittest.TestCase):
    def setUp(self):
        module_path = Path(__file__).resolve().parents[1] / "http.py"
        spec = importlib.util.spec_from_file_location("opalib_http", module_path)
        self.http_module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(self.http_module)

    def test_get_request(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, format, *args):
                return

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/"
            result = {}
            event = threading.Event()

            def on_success(promise, arg):
                result["response"] = arg
                event.set()

            def on_error(promise, arg):
                result["error"] = arg
                event.set()

            promise = self.http_module.req({"Url": url, "Method": "GET"})
            promise.Then(on_success).Else(on_error)

            self.assertTrue(event.wait(5), "HTTP request did not complete in time")
            self.assertIn("response", result)
            self.assertEqual(result["response"]["StatusCode"], 200)
            self.assertEqual(result["response"]["Body"], "ok")
        finally:
            server.shutdown()
            thread.join(timeout=1)
