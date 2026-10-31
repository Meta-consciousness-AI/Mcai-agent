import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from mcai import server

ROOT = Path(__file__).resolve().parent.parent
TOKEN = "test-token"


class McpHttpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = type("TestHandler", (server.Handler,), {
            "root": ROOT,
            "token": TOKEN,
            "limiter": server.RateLimiter(600),
            "cors_origin": "*",
        })
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _post(self, payload, token=TOKEN):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/mcp",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {token}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_initialize(self):
        status, data = self._post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(status, 200)
        self.assertEqual(data["result"]["serverInfo"]["name"], "mcai-knowledge")

    def test_tools_list(self):
        status, data = self._post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertEqual(status, 200)
        self.assertEqual(len(data["result"]["tools"]), 5)

    def test_tool_call_citations(self):
        status, data = self._post({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "mcai_answer",
                       "arguments": {"question": "什么是元识", "format": "citations"}},
        })
        self.assertEqual(status, 200)
        payload = json.loads(data["result"]["content"][0]["text"])
        self.assertTrue(payload["citations"])
        self.assertNotIn("answer", payload)

    def test_batch(self):
        status, data = self._post([
            {"jsonrpc": "2.0", "id": 4, "method": "ping"},
            {"jsonrpc": "2.0", "id": 5, "method": "ping"},
        ])
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 2)

    def test_get_not_allowed(self):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/mcp",
                                     headers={"Authorization": f"Bearer {TOKEN}"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 405)

    def test_auth_required(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post({"jsonrpc": "2.0", "id": 6, "method": "ping"}, token="wrong")
        self.assertEqual(ctx.exception.code, 401)


if __name__ == "__main__":
    unittest.main()
