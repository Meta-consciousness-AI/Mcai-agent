# -*- coding: utf-8 -*-
import socket
import unittest
import urllib.error

from tools import daily_signal


class FmtErrTest(unittest.TestCase):
    def test_http_403_is_rate_limit(self):
        e = urllib.error.HTTPError("u", 403, "Forbidden", {}, None)
        self.assertIn("限流", daily_signal.fmt_err(e))

    def test_http_500_is_server_error(self):
        e = urllib.error.HTTPError("u", 503, "Unavailable", {}, None)
        self.assertIn("服务端", daily_signal.fmt_err(e))

    def test_timeout(self):
        e = urllib.error.URLError(socket.timeout("timed out"))
        self.assertIn("超时", daily_signal.fmt_err(e))

    def test_connection(self):
        e = urllib.error.URLError(ConnectionResetError("reset"))
        self.assertIn("连接失败", daily_signal.fmt_err(e))


class CacheTest(unittest.TestCase):
    def test_failure_shows_last(self):
        cache = {}
        line = daily_signal.with_last(cache, "PyPI", "PyPI：查询失败（超时）", True, "0.3.9")
        self.assertEqual(line, "PyPI：查询失败（超时）")
        self.assertEqual(cache["PyPI"]["value"], "0.3.9")
        line2 = daily_signal.with_last(cache, "PyPI", "PyPI：查询失败（超时）", False, None)
        self.assertIn("上次", line2)
        self.assertIn("0.3.9", line2)

    def test_success_no_prev(self):
        cache = {}
        line = daily_signal.with_last(cache, "X", "X：查询失败", False, None)
        self.assertEqual(line, "X：查询失败")


if __name__ == "__main__":
    unittest.main()
