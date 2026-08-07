from __future__ import annotations

import re
from datetime import date
from urllib.parse import urlparse

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.-]?)?(?:\(\d{1,4}\)[\s.-]?)?\d{3}[\s.-]?\d{3,4}[\s.-]?\d{4}"
)
_URL_RE = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+")

_BULLET_RE = re.compile(r"^\s*[-*•→‣▸▪●·o]+\s+")
_NUMBERED_BULLET_RE = re.compile(r"^\s*\d{1,2}[.)]\s+")
_DIVIDER_RE = re.compile(r"^\s*[-_=*•#]{3,}\s*$")
_CODE_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_MARKDOWN_HEADER_RE = re.compile(r"^\s*#{1,6}\s*")
_INLINE_MARKDOWN_RE = re.compile(r"\*\*|__|~~|`")
_BLOCKQUOTE_RE = re.compile(r"^\s*>\s?")

_SUBJECT_RE = re.compile(r"^Subject\s*:", re.IGNORECASE)

_PREAMBLE_PHRASES = (
    "here is",
    "here's",
    "here are",
    "below is",
    "below, i",
    "below i",
    "okay,",
    "sure, here",
    "certainly,",
    "certainly!",
    "as requested",
    "i have drafted",
    "i've drafted",
    "i have written",
    "i've written",
    "i have prepared",
    "i've prepared",
    "i have created",
    "i've created",
    "drafted based",
    "generated based",
    "you requested",
    "based on the job posting",
    "incorporating the analysis",
    "taking into account",
    "the tailored resume",
    "the cover letter is",
    "your tailored resume",
)

_COVER_TRAILING_RE = re.compile(
    r"^\s*[*\-•→‣▸▪●]?\s*(Explanation|Rationale|What I changed|Why I|Key changes|"
    r"Analysis|Notes?|Review|I'?ve (also )?(significantly|enhanced|rewritten)|"
    r"I have (also )?(significantly|enhanced|rewritten))\b",
    re.IGNORECASE,
)

_RESUME_TRAILING_RE = re.compile(
    r"^\s*[*\-•→‣▸▪●]?\s*(Note\b.*|I'?ve (significantly|enhanced|rewritten|tailored)|"
    r"I have (significantly|enhanced|rewritten|tailored)|"
    r"Additionally,? I (have|added)|Please (review|let me)|Let me know|Hope this)\b",
    re.IGNORECASE,
)

_SALUTATION_RE = re.compile(r"^(Dear|To|Hello|Greetings|Hi)\s", re.IGNORECASE)
_CLOSING_RE = re.compile(
    r"^(Sincerely|Best\s+(?:regards|wishes)|Yours\s+(?:truly|sincerely|faithfully)|"
    r"Thanks?|Respectfully|Cordially|Warm(?:ly)?|"
    r"Kind\s+regards|Regards|With\s+(?:gratitude|appreciation|thanks))",
    re.IGNORECASE,
)

_PLACEHOLDERS: dict[str, str] = {
    "your full name": "name",
    "your name": "name",
    "candidate name": "name",
    "your address": "address",
    "your city": "location",
    "your location": "location",
    "city, state": "location",
    "your phone number": "phone",
    "phone number": "phone",
    "your email address": "email",
    "email address": "email",
    "your email": "email",
    "date": "date",
    "today's date": "date",
    "current date": "date",
    "company name": "company",
    "company": "company",
    "hiring manager": "recipient",
    "recipient": "recipient",
}

_JOB_BOARD_HOSTS = frozenset(
    {
        "lever", "greenhouse", "ashbyhq", "workable", "jobvite", "icims",
        "smartrecruiters", "bamboohr", "paycomonline", "ultipro", "workday",
        "myworkdayjobs", "linkedin", "indeed", "ziprecruiter", "glassdoor",
        "monster", "weworkremotely", "careers", "jobs", "job", "apply",
        "recruiting", "jobboard", "talent", "teamtailor",
    }
)

_COMPANY_FROM_TEXT_PATTERNS = (
    re.compile(r"(?:^|\n)company[:：]\s*([^\n,]+)", re.IGNORECASE),
    re.compile(r"(?:^|\n)employer[:：]\s*([^\n,]+)", re.IGNORECASE),
    re.compile(r"(?:^|\n)organization[:：]\s*([^\n,]+)", re.IGNORECASE),
    re.compile(r"\b(at|with)\s+([A-Z][A-Za-z0-9&.'-]+(?:\s+[A-Z][A-Za-z0-9&.'-]*){0,2})\s+is\s+hiring\b"),
    re.compile(r"\b([A-Z][A-Za-z0-9&.'-]+(?:\s+[A-Z][A-Za-z0-9&.'-]*){0,2})\s+is\s+hiring\b"),
    re.compile(r"\bhiring\s+(?:at|for)\s+([A-Z][A-Za-z0-9&.'-]+(?:\s+[A-Z][A-Za-z0-9&.'-]*){0,2})\b"),
)

_GENERIC_WORDS = frozenset(
    {"the", "our", "we", "you", "a", "an", "your", "this", "that", "team",
     "company", "who", "what", "are", "being", "role", "position", "job"}
)


def fix_tabs(text: str) -> str:
    return text.replace("\t", "  ")


def normalize_bullets(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    for line in lines:
        if _NUMBERED_BULLET_RE.match(line):
            line = _NUMBERED_BULLET_RE.sub("- ", line)
        elif _BULLET_RE.match(line):
            line = _BULLET_RE.sub("- ", line)
        out.append(line)
    return "\n".join(out)


def strip_markdown(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    in_code = False
    for line in lines:
        if _CODE_FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        if _DIVIDER_RE.match(line):
            continue
        line = _BLOCKQUOTE_RE.sub("", line)
        line = _MARKDOWN_HEADER_RE.sub("", line)
        line = _INLINE_MARKDOWN_RE.sub("", line)
        line = line.replace("*", "")
        out.append(line)
    return "\n".join(out)


def _looks_like_preamble(block: str) -> bool:
    lowered = block.strip().lower()
    if not lowered:
        return False
    return any(phrase in lowered for phrase in _PREAMBLE_PHRASES)


def strip_preamble(text: str, doc_kind: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    start = 0
    for i, block in enumerate(blocks):
        if not _looks_like_preamble(block):
            start = i
            break
    return "\n\n".join(blocks[start:])


def strip_letter_header(body: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
    subject: str | None = None
    salutation_idx = None
    for i, block in enumerate(blocks):
        if _SUBJECT_RE.match(block):
            subject = block
            continue
        if _SALUTATION_RE.match(block):
            salutation_idx = i
            break
    if salutation_idx is None:
        return body
    result = blocks[salutation_idx:]
    if subject is not None:
        result = [subject] + result
    return "\n\n".join(result)


def strip_trailing_notes(text: str, doc_kind: str) -> str:
    pattern = _COVER_TRAILING_RE if doc_kind == "cover" else _RESUME_TRAILING_RE
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if pattern.match(line):
            return "\n".join(lines[:i]).strip()
    return text


def _remove_trailing_signature(body: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
    if not blocks:
        return body
    last = blocks[-1]
    if _CLOSING_RE.match(last):
        lines = last.split("\n")
        cut = 1
        for i, line in enumerate(lines):
            if _CLOSING_RE.match(line.strip()):
                cut = i + 1
        blocks[-1] = "\n".join(lines[:cut]).strip()
        return "\n\n".join(blocks).strip()
    if len(blocks) >= 2 and _CLOSING_RE.match(blocks[-2]):
        return "\n\n".join(blocks[:-1]).strip()
    return body.strip()


def _today_str() -> str:
    return date.today().strftime("%B %d, %Y").replace(" 0", " ")


def replace_placeholders(text: str, contact: dict[str, str | None]) -> str:
    values: dict[str, str] = {}
    for key, field in _PLACEHOLDERS.items():
        value = contact.get(field)
        if value:
            values[key] = value
    values["date"] = _today_str()
    if not contact.get("company"):
        values["company"] = "Hiring Manager"
    if not values.get("recipient"):
        values["recipient"] = "Hiring Manager"

    def _repl(match: re.Match) -> str:
        token = match.group(1).strip().lower()
        if token in values:
            return values[token]
        if token in _PLACEHOLDERS:
            return ""
        return match.group(0)

    text = re.sub(r"\[([^\]]+)\]", _repl, text)
    lines = [
        line for line in text.split("\n")
        if line.strip() not in ("Your Name", "Your Address")
    ]
    return collapse_blank_lines("\n".join(lines))


def collapse_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text.strip())


def parse_contact_from_resume(resume_text: str) -> dict[str, str]:
    lines = [l.strip() for l in resume_text.split("\n") if l.strip()]
    name = lines[0] if lines else ""
    emails = _EMAIL_RE.findall(resume_text)
    phones = _PHONE_RE.findall(resume_text)
    urls = [u for u in _URL_RE.findall(resume_text) if "github.com" in u or "linkedin.com" in u]

    location = ""
    for line in lines[1:3]:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            candidate = parts[0]
            if (
                candidate
                and not _EMAIL_RE.match(candidate)
                and not _PHONE_RE.match(candidate)
                and not _URL_RE.match(candidate)
                and re.search(r"[A-Za-z]", candidate)
            ):
                location = candidate
                break

    return {
        "name": name,
        "phone": phones[0] if phones else "",
        "email": emails[0] if emails else "",
        "location": location,
        "urls": " | ".join(urls),
    }


def _title_case(company: str) -> str:
    words = company.split()
    kept = [w for w in words if w.lower() not in _GENERIC_WORDS]
    if not kept:
        kept = words
    result = " ".join(w.capitalize() for w in kept)
    return result if len(result) > 2 else company


def detect_company(job_text: str | None, url: str | None = None) -> str | None:
    if url:
        try:
            host = urlparse(url).netloc.lower()
            host = host.split("@")[-1].split(":")[0]
            for prefix in ("www.", "careers.", "jobs."):
                if host.startswith(prefix):
                    host = host[len(prefix):]
            parts = [p for p in host.split(".") if p]
            if len(parts) >= 2 and parts[-1] in {"com", "org", "net", "io", "ai", "co", "dev", "jobs", "careers"}:
                parts = parts[:-1]
            parts = [p for p in parts if p not in _JOB_BOARD_HOSTS]
            if parts:
                return parts[-1].title()
        except ValueError:
            pass

    if job_text:
        candidates: list[str] = []
        for pattern in _COMPANY_FROM_TEXT_PATTERNS:
            matches = pattern.findall(job_text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[-1]
                candidate = match.strip()
                if candidate and candidate.lower() not in _GENERIC_WORDS:
                    candidates.append(candidate)
        if candidates:
            counts: dict[str, int] = {}
            for candidate in candidates:
                key = candidate.lower()
                counts[key] = counts.get(key, 0) + 1
            best = max(counts, key=counts.get)
            if counts[best] == 1 and len(candidates) > 1:
                return None
            return _title_case(best)
    return None


def build_letter_header(
    contact: dict[str, str],
    company: str | None = None,
    today: str | None = None,
) -> dict[str, str]:
    contact_line = " | ".join(
        part for part in (contact.get("location", ""), contact.get("phone", ""),
                          contact.get("email", ""), contact.get("urls", ""))
        if part
    )
    recipient = "Hiring Manager"
    if company:
        recipient = f"Hiring Manager\n{company}"
    return {
        "name": contact.get("name", ""),
        "contact": contact_line,
        "date": today or _today_str(),
        "recipient": recipient,
    }


def compose_cover_letter(header: dict[str, str], body: str) -> str:
    parts: list[str] = []
    if header.get("name"):
        parts.append(header["name"])
    if header.get("contact"):
        parts.append(header["contact"])
    if parts:
        parts.append(header.get("date", ""))
    if header.get("recipient"):
        parts.append(header["recipient"])

    clean_body = _remove_trailing_signature(body.strip())
    if not _CLOSING_RE.match(clean_body.splitlines()[-1].strip()):
        clean_body = clean_body.rstrip() + "\n\nSincerely,"

    parts.append(clean_body)
    parts.append(header.get("name", ""))

    return "\n\n".join(p for p in parts if p)


def normalize_output(
    text: str,
    doc_kind: str,
    contact: dict[str, str | None] | None = None,
    company: str | None = None,
) -> str:
    cleaned = fix_tabs(text)
    cleaned = normalize_bullets(cleaned)
    cleaned = strip_markdown(cleaned)
    cleaned = strip_preamble(cleaned, doc_kind)
    if doc_kind == "cover":
        cleaned = strip_letter_header(cleaned)
    cleaned = strip_trailing_notes(cleaned, doc_kind)
    if doc_kind == "cover" and contact:
        contact = dict(contact)
        contact["company"] = company or ""
        cleaned = replace_placeholders(cleaned, contact)
    return collapse_blank_lines(cleaned)


def normalize_resume(text: str) -> str:
    return normalize_output(text, "resume")


def normalize_cover_body(text: str, contact: dict[str, str], company: str | None) -> str:
    return normalize_output(text, "cover", contact=contact, company=company)
