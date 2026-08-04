from __future__ import annotations

import ipaddress
import socket
import time

import pytest
import requests

from pocket_r2 import scraper


class FakeResponse:
    def __init__(
        self,
        status_code=200,
        headers=None,
        content=b"",
        url="http://example.com/",
    ):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content
        self.url = url
        self.encoding = "utf-8"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def iter_content(self, chunk_size=65536):
        for i in range(0, len(self.content), chunk_size):
            yield self.content[i : i + chunk_size]


def test_ip_is_blocked():
    assert scraper._ip_is_blocked(ipaddress.ip_address("10.0.0.1")) is True
    assert scraper._ip_is_blocked(ipaddress.ip_address("169.254.169.254")) is True
    assert scraper._ip_is_blocked(ipaddress.ip_address("::ffff:192.168.1.1")) is True
    assert scraper._ip_is_blocked(ipaddress.ip_address("8.8.8.8")) is False


def test_is_blocked_url_raw_private_ip():
    assert scraper._is_blocked_url("http://127.0.0.1/admin") is True
    assert scraper._is_blocked_url("http://10.0.0.5") is True


def test_is_blocked_url_bad_scheme():
    assert scraper._is_blocked_url("file:///etc/passwd") is True
    assert scraper._is_blocked_url("ftp://example.com/x") is True


def test_resolve_host_blocked_blocks_private_dns(monkeypatch):
    def fake_getaddrinfo(host, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.10", 0))]

    monkeypatch.setattr(scraper.socket, "getaddrinfo", fake_getaddrinfo)
    assert scraper._resolve_host_blocked("private.example") is True


def test_resolve_host_blocked_fails_closed_on_gaierror(monkeypatch):
    def fake_getaddrinfo(host, *args, **kwargs):
        raise socket.gaierror("nope")

    monkeypatch.setattr(scraper.socket, "getaddrinfo", fake_getaddrinfo)
    assert scraper._resolve_host_blocked("bad.invalid") is True


def test_resolve_host_blocked_fails_closed_on_timeout(monkeypatch):
    def slow_getaddrinfo(host, *args, **kwargs):
        time.sleep(1)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.2.3.4", 0))]

    monkeypatch.setattr(scraper.socket, "getaddrinfo", slow_getaddrinfo)
    assert scraper._resolve_host_blocked("slow.example", timeout=0.05) is True


def test_redirect_to_private_raises_blocked(monkeypatch):
    def fake_get(url, **kwargs):
        return FakeResponse(
            status_code=302,
            headers={"Location": "http://127.0.0.1/admin"},
            url=url,
        )

    monkeypatch.setattr(scraper.requests, "get", fake_get)
    with pytest.raises(scraper.BlockedURLError):
        scraper.fetch_static("http://example.com/job", allow_private_urls=False)


def test_read_limited_rejects_oversized_body():
    resp = FakeResponse(content=b"x" * 5000, url="http://example.com/big")
    with pytest.raises(scraper.ContentTooLargeError):
        scraper._read_limited(resp, max_bytes=1000)


def test_read_limited_rejects_via_content_length():
    resp = FakeResponse(
        headers={"Content-Length": "999999999999"},
        content=b"",
        url="http://example.com/big",
    )
    with pytest.raises(scraper.ContentTooLargeError):
        scraper._read_limited(resp, max_bytes=1000)


def test_fetch_static_returns_text_for_valid_page(monkeypatch):
    html = "<html><body><p>" + ("job text " * 40) + "</p></body></html>"
    resp = FakeResponse(content=html.encode(), url="http://example.com/job")
    monkeypatch.setattr(scraper.requests, "get", lambda *a, **kw: resp)
    text = scraper.fetch_static("http://example.com/job")
    assert text is not None and "job text" in text


def test_fetch_static_returns_none_for_tiny_page(monkeypatch):
    resp = FakeResponse(
        content=b"<html><body>short</body></html>", url="http://example.com/job"
    )
    monkeypatch.setattr(scraper.requests, "get", lambda *a, **kw: resp)
    assert scraper.fetch_static("http://example.com/job") is None
