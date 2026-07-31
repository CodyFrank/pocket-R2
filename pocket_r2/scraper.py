from __future__ import annotations

import ipaddress
import socket
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

MIN_CONTENT_LENGTH = 200
MAX_REDIRECTS = 5
_REDIRECT_CODES = (301, 302, 303, 307, 308)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
}

# SSRF guard: URLs that resolve to non-public addresses are refused before any
# request is made. This blocks access to internal services (localhost, RFC1918,
# link-local), cloud metadata endpoints (169.254.169.254), and NAT64-mapped
# private addresses.
#
# Residual risk (accepted, Layer 4 deferred): DNS rebinding. A domain could
# alternate between a public and a private IP between validation and the actual
# connection (TOCTOU). Fully closing this requires pinning the resolved IP at
# connection time, which breaks CDN routing, proxies, and dual-stack failover,
# and would not cover Playwright (the browser resolves its own DNS). This is a
# low residual risk for a CLI tool that fetches user-supplied job URLs.


class BlockedURLError(Exception):
    def __init__(self, url: str) -> None:
        super().__init__(
            f"Refusing to fetch {url}: it resolves to a private or reserved "
            "address (SSRF guard). Use --allow-private-urls to override "
            "(unsafe), or paste the job posting text with --text."
        )


_BLOCKED_HOST_CACHE: dict[str, bool] = {}


def _ip_is_blocked(ip) -> bool:
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return not ip.is_global or ip.is_multicast or ip.is_reserved


def _resolve_host_blocked(host: str) -> bool:
    try:
        addrinfos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return True
    if not addrinfos:
        return True
    for info in addrinfos:
        ip_str = info[4][0].split("%")[0]
        if _ip_is_blocked(ipaddress.ip_address(ip_str)):
            return True
    return False


def _is_blocked_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return True
    host = parsed.hostname
    if not host:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        cached = _BLOCKED_HOST_CACHE.get(host)
        if cached is not None:
            return cached
        blocked = _resolve_host_blocked(host)
        _BLOCKED_HOST_CACHE[host] = blocked
        return blocked
    return _ip_is_blocked(ip)


def fetch_static(url: str, allow_private_urls: bool = False) -> str | None:
    """Fetch page with requests + BeautifulSoup. Returns extracted text or None."""
    current = url
    try:
        for _ in range(MAX_REDIRECTS):
            resp = requests.get(
                current,
                timeout=15,
                headers=_HEADERS,
                allow_redirects=False,
            )
            if resp.status_code in _REDIRECT_CODES:
                location = resp.headers.get("Location")
                if not location:
                    return None
                current = urljoin(current, location)
                if not allow_private_urls and _is_blocked_url(current):
                    raise BlockedURLError(current)
                continue
            break
        else:
            return None
        resp.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text if len(text) >= MIN_CONTENT_LENGTH else None


def fetch_with_playwright(url: str, allow_private_urls: bool = False) -> str | None:
    """Fetch page with Playwright (renders JS). Returns extracted text or None."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Playwright not installed. Install it with:\n"
            "  pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        return None

    def _route_handler(route) -> None:
        if not allow_private_urls and _is_blocked_url(route.request.url):
            route.abort()
        else:
            route.continue_()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage"],
            )
            page = browser.new_page()
            page.route("**/*", _route_handler)
            page.goto(url, wait_until="networkidle", timeout=30000)
            content = page.content()
            browser.close()
    except Exception:
        return None

    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text if len(text) >= MIN_CONTENT_LENGTH else None


def fetch_job_posting(url: str, allow_private_urls: bool = False) -> str:
    """Fetch a job posting from a URL. Tries static first, then Playwright."""
    print(f"Fetching: {url}", file=sys.stderr)

    if not allow_private_urls and _is_blocked_url(url):
        raise SystemExit(str(BlockedURLError(url)))

    try:
        text = fetch_static(url, allow_private_urls)
    except BlockedURLError as exc:
        raise SystemExit(str(exc))

    if text:
        print("Fetched via static request.", file=sys.stderr)
        return text

    print("Static fetch insufficient, trying Playwright...", file=sys.stderr)
    try:
        text = fetch_with_playwright(url, allow_private_urls)
    except BlockedURLError as exc:
        raise SystemExit(str(exc))

    if text:
        print("Fetched via Playwright.", file=sys.stderr)
        return text

    raise SystemExit(
        "Could not extract content from the URL.\n"
        "Try copying the job posting text and using --text instead."
    )


def get_job_text(
    url: str | None = None,
    text: str | None = None,
    allow_private_urls: bool = False,
) -> str:
    """Get job posting text from URL or raw text input."""
    if text:
        return text.strip()
    if url:
        return fetch_job_posting(url, allow_private_urls)
    raise ValueError("Provide either --url or --text")
