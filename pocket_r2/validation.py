from __future__ import annotations

import json
import re

from pocket_r2.llm import generate
from pocket_r2.prompts import build_validation_messages

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.-]?)?(?:\(\d{1,4}\)[\s.-]?)?\d{3}[\s.-]?\d{3,4}[\s.-]?\d{4}"
)
_URL_RE = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+")
_HANDLE_RE = re.compile(r"@[A-Za-z0-9_]{1,15}")

_SUSPICIOUS_KEYWORDS = (
    "ignore previous",
    "system override",
    "you are now",
    "forget everything",
    "override mode",
    "disregard prior",
    "ignore the system",
    "act as",
    "print this",
    "reveal your instructions",
)


def extract_contact_info(text: str) -> set[str]:
    found: set[str] = set()
    for regex in (_EMAIL_RE, _PHONE_RE, _URL_RE, _HANDLE_RE):
        found.update(regex.findall(text))
    return found


def basic_contact_check(output: str, resume_text: str) -> list[str]:
    """Return flags for contact info/URLs in output not present in the resume."""
    trusted = extract_contact_info(resume_text)
    flags: list[str] = []
    for item in sorted(extract_contact_info(output) - trusted):
        flags.append(f"contact/URL '{item}' not present in the resume")
    lowered = output.lower()
    for keyword in _SUSPICIOUS_KEYWORDS:
        if keyword in lowered:
            flags.append(f"suspicious phrasing '{keyword}'")
    return flags


def parse_validator_json(text: str) -> dict | None:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return data
    return None


def validate_output(
    job_text: str,
    resume_text: str,
    output: str,
    model: str,
    provider: str,
    host: str | None,
) -> tuple[bool, str]:
    """Ask the LLM to judge whether output contains injected/fabricated content.

    Returns (ok, reason). Fails open if the validator itself errors out —
    callers rely on the deterministic layer as well.
    """
    try:
        messages = build_validation_messages(job_text, resume_text, output)
        verdict = generate(messages, model=model, provider=provider, host=host)
    except Exception:
        return True, "validator unavailable"
    data = parse_validator_json(verdict)
    if data is None:
        return True, "validator returned unparseable verdict"
    if data.get("ok") is True or str(data.get("ok", "")).lower() == "true":
        return True, str(data.get("reason", "") or "clean")
    return False, str(data.get("reason", "") or "flagged by validator")
