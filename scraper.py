from __future__ import annotations

import sys
import textwrap

import requests
from bs4 import BeautifulSoup

MIN_CONTENT_LENGTH = 200


def fetch_static(url: str) -> str | None:
    """Fetch page with requests + BeautifulSoup. Returns extracted text or None."""
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        })
        resp.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text if len(text) >= MIN_CONTENT_LENGTH else None


def fetch_with_playwright(url: str) -> str | None:
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

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
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


def fetch_job_posting(url: str) -> str:
    """Fetch a job posting from a URL. Tries static first, then Playwright."""
    print(f"Fetching: {url}", file=sys.stderr)

    text = fetch_static(url)
    if text:
        print("Fetched via static request.", file=sys.stderr)
        return text

    print("Static fetch insufficient, trying Playwright...", file=sys.stderr)
    text = fetch_with_playwright(url)
    if text:
        print("Fetched via Playwright.", file=sys.stderr)
        return text

    raise SystemExit(
        "Could not extract content from the URL.\n"
        "Try copying the job posting text and using --text instead."
    )


def get_job_text(url: str | None = None, text: str | None = None) -> str:
    """Get job posting text from URL or raw text input."""
    if text:
        return text.strip()
    if url:
        return fetch_job_posting(url)
    raise ValueError("Provide either --url or --text")
