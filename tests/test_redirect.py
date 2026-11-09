import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from mcai import server

ROOT = Path(__file__).resolve().parent.parent


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class _Recorder:
    def __init__(self):
        self.calls = []

    def record(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class RedirectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recorder = _Recorder()
        cls._orig = server.telemetry.for_root
        server.telemetry.for_root = lambda root: cls.recorder

        handler = type("RedirectHandler", (server.Handler,), {
            "root": ROOT,
            "token": "",
            "limiter": server.RateLimiter(600),
            "cors_origin": "*",
        })
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.opener = urllib.request.build_opener(_NoRedirect)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        server.telemetry.for_root = cls._orig

    def _get(self, path):
        try:
            return self.opener.open(f"http://127.0.0.1:{self.port}{path}", timeout=10)
        except urllib.error.HTTPError as exc:
            return exc

    def test_redirects_and_records_source(self):
        self.recorder.calls.clear()
        res = self._get("/r?src=kuaishou")
        self.assertEqual(res.code, 302)
        self.assertIn("from=kuaishou", res.headers.get("Location", ""))
        self.assertTrue(any(call[0][:3] == ("redirect", "visit", "kuaishou") for call in self.recorder.calls))

    def test_long_path_source_is_kept(self):
        self.recorder.calls.clear()
        src = "p-concepts-meta-consciousness-interpretation"
        res = self._get("/r?src=" + src)
        self.assertEqual(res.code, 302)
        self.assertIn("from=" + src, res.headers.get("Location", ""))
        self.assertTrue(any(call[0][:3] == ("redirect", "visit", src) for call in self.recorder.calls))

    def test_invalid_source_falls_back_to_unknown(self):
        self.recorder.calls.clear()
        res = self._get("/r?src=" + "x" * 80)
        self.assertEqual(res.code, 302)
        self.assertIn("from=unknown", res.headers.get("Location", ""))
        self.assertTrue(any(call[0][:3] == ("redirect", "visit", "unknown") for call in self.recorder.calls))


if __name__ == "__main__":
    unittest.main()
