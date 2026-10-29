# -*- coding: utf-8 -*-
"""安全暴露测试：令牌、限流、CORS、本机专属接口、访问日志。"""
import json
import shutil
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai.server import Handler, RateLimiter, is_local_ip  # noqa: E402

TOKEN = "test-token-123"


class UnitTest(unittest.TestCase):
    def test_is_local_ip(self) -> None:
        self.assertTrue(is_local_ip("127.0.0.1"))
        self.assertTrue(is_local_ip("::1"))
        self.assertFalse(is_local_ip("8.8.8.8"))

    def test_rate_limiter(self) -> None:
        limiter = RateLimiter(limit=2, window=60)
        self.assertTrue(limiter.allow("a"))
        self.assertTrue(limiter.allow("a"))
        self.assertFalse(limiter.allow("a"))
        self.assertTrue(limiter.allow("b"))


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.work = Path(__file__).parent / "_work_http"
        shutil.rmtree(cls.work, ignore_errors=True)
        (cls.work / "dist").mkdir(parents=True)
        (cls.work / "data").mkdir(parents=True)
        (cls.work / "dist" / "index.html").write_text("<html>ok</html>", encoding="utf-8")
        shutil.copyfile(ROOT / "data" / "kb.json", cls.work / "data" / "kb.json")

        handler = type("TestHandler", (Handler,), {
            "root": cls.work,
            "token": TOKEN,
            "limiter": RateLimiter(500),
            "cors_origin": "*",
        })
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        shutil.rmtree(cls.work, ignore_errors=True)

    def url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def get(self, path: str, token: str | None = None) -> tuple[int, dict]:
        req = urllib.request.Request(self.url(path))
        if token is not None:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            return exc.code, json.loads(body) if body.startswith("{") else {}

    def test_api_requires_token(self) -> None:
        status, payload = self.get("/api/v1/answer?q=%E4%BB%80%E4%B9%88%E6%98%AF%E5%85%83%E6%84%8F%E8%AF%86")
        self.assertEqual(status, 401)
        self.assertFalse(payload.get("ok"))

    def test_api_accepts_valid_token(self) -> None:
        status, payload = self.get(
            "/api/v1/answer?q=%E4%BB%80%E4%B9%88%E6%98%AF%E5%85%83%E6%84%8F%E8%AF%86", token=TOKEN
        )
        self.assertEqual(status, 200)
        self.assertIn(payload["type"], ("faq", "concept"))

    def test_wrong_token_rejected(self) -> None:
        status, _ = self.get("/api/v1/answer?q=test", token="wrong")
        self.assertEqual(status, 401)

    def test_health_is_public(self) -> None:
        status, payload = self.get("/api/v1/health")
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["auth_required"])

    def test_static_site_is_public(self) -> None:
        with urllib.request.urlopen(self.url("/"), timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("ok", resp.read().decode("utf-8"))

    def test_options_cors(self) -> None:
        req = urllib.request.Request(self.url("/api/v1/answer"), method="OPTIONS")
        with urllib.request.urlopen(req, timeout=10) as resp:
            self.assertEqual(resp.status, 204)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

    def test_cors_on_json(self) -> None:
        with urllib.request.urlopen(self.url("/api/v1/health"), timeout=10) as resp:
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

    def test_access_log_written_without_token(self) -> None:
        self.get("/api/v1/health")
        log_path = self.work / "data" / "access.log"
        self.assertTrue(log_path.exists())
        text = log_path.read_text(encoding="utf-8")
        self.assertIn("/api/v1/health", text)
        self.assertNotIn(TOKEN, text)


if __name__ == "__main__":
    unittest.main()
