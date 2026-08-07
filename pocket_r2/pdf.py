from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

FONT_DIR = Path(__file__).parent / "fonts"

_SECTION_KEYWORDS = frozenset({
    "experience", "education", "skills", "summary", "profile",
    "objective", "projects", "certifications", "publications",
    "awards", "honors", "interests", "languages", "volunteer",
    "leadership", "accomplishments", "achievements",
    "tools", "qualifications", "employment", "work history",
    "professional experience", "professional summary",
    "technical skills", "additional", "references",
})

_DATE_RE = re.compile(
    r"^(?:January|February|March|April|May|June|"
    r"July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}$"
)

_SALUTATION_RE = re.compile(r"^(Dear|To|Hello|Greetings|Hi)\s", re.IGNORECASE)

_SUBJECT_RE = re.compile(r"^Subject\s*:", re.IGNORECASE)

_CLOSING_RE = re.compile(
    r"^(Sincerely|Best\s+(?:regards|wishes)|Yours\s+(?:truly|sincerely|faithfully)|"
    r"Thanks?|Respectfully|Cordially|Warm(?:ly)?|"
    r"Kind\s+regards|Regards|With\s+(?:gratitude|appreciation|thanks))",
    re.IGNORECASE,
)

_BULLET_RE = re.compile(r"^[-*•→‣▸▪●]\s*")

_MARKDOWN_HEADER_RE = re.compile(r"^#{1,3}\s+\w")

_JOB_DATE_RE = re.compile(
    r"(?:19|20)\d{2}\s*[-–—to]+\s*(?:(?:19|20)\d{2}|Present|Current|Now)",
    re.IGNORECASE,
)

_DIVIDER_RE = re.compile(r"^[-_=•*]{3,}$")

_HEADLINE_KEYWORDS = (
    "engineer", "developer", "analyst", "scientist", "manager", "lead",
    "architect", "designer", "specialist", "consultant", "administrator",
    "annotator", "director", "coordinator", "officer", "assistant",
    "researcher", "instructor", "writer", "editor", "producer", "operator",
    "technician", "intern", "sales", "support", "advisor", "founder", "owner",
)


def _clean_text(text: str) -> str:
    text = text.replace("\t", "  ")
    text = re.sub(r"\*\*|`", "", text)
    text = re.sub(r"(?<![\w*])\*(?![\w*])", "", text)
    return text


def _is_date_block(text: str) -> bool:
    return bool(_DATE_RE.match(text.strip()))


def _is_salutation_block(text: str) -> bool:
    return bool(_SALUTATION_RE.match(text.strip()))


def _is_closing_block(text: str) -> bool:
    for line in text.strip().split("\n"):
        if _CLOSING_RE.match(line.strip()):
            return True
    return False


def _is_section_header_line(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 55 or "|" in s:
        return False
    if _MARKDOWN_HEADER_RE.match(s):
        return True
    if s.isupper() and len(s.split()) <= 5:
        return True
    if s.lower().rstrip(":").strip() in _SECTION_KEYWORDS:
        return True
    return False


def _is_headline(line: str) -> bool:
    s = line.strip()
    if not s or "|" not in s or len(s) > 60:
        return False
    return any(k in s.lower() for k in _HEADLINE_KEYWORDS)


def _is_bullet(line: str) -> bool:
    return bool(_BULLET_RE.match(line.strip()))


def _split_job_entry(line: str) -> dict[str, str]:
    parts = [p.strip() for p in line.split("|")]
    title = parts[0] if parts else line.strip()
    company = parts[1] if len(parts) > 1 else ""
    location = parts[2] if len(parts) > 2 else ""
    dates = parts[3] if len(parts) > 3 else ""
    return {"title": title, "company": company, "location": location, "dates": dates}


def _is_job_entry(line: str) -> bool:
    s = _BULLET_RE.sub("", line.strip()).strip()
    if not s:
        return False
    if "|" in s:
        parts = [p.strip() for p in s.split("|")]
        if len(parts) >= 2:
            if _JOB_DATE_RE.search(s) or len(parts) >= 3:
                return True
            if any(k in parts[0].lower() for k in _HEADLINE_KEYWORDS):
                return True
    if _JOB_DATE_RE.search(s):
        return True
    return False


class _PDF(FPDF):
    MARGIN = 25

    def __init__(self, page_format: str = "Letter") -> None:
        super().__init__(format=page_format)
        self.add_font("DejaVu", "", str(FONT_DIR / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"))
        self.set_auto_page_break(auto=True, margin=self.MARGIN)

    @property
    def _bw(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def _mc(self, h: float, text: str, align: str = "L") -> None:
        self.set_x(self.l_margin)
        self.multi_cell(self._bw, h, _clean_text(text), align=align)

    def footer(self) -> None:
        self.set_y(-20)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, str(self.page_no()), align="C")

    def _begin(self) -> None:
        self.add_page()
        self.set_margins(self.MARGIN, self.MARGIN, self.MARGIN)
        self.set_text_color(30, 30, 30)


class CoverLetterPDF(_PDF):
    def render(self, text: str) -> CoverLetterPDF:
        self._begin()
        blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
        state = "header"

        for block in blocks:
            if state == "header":
                if _is_date_block(block):
                    self._date(block)
                elif _is_salutation_block(block):
                    self._salutation(block)
                    state = "body"
                else:
                    self._paragraph(block)
                    state = "body"
            elif state == "body":
                if _is_closing_block(block):
                    self._closing(block)
                    state = "closing"
                else:
                    self._paragraph(block)
            elif state == "closing":
                self._signature(block)
            else:
                self._paragraph(block)
        return self

    def render_with_header(
        self, header: dict[str, str], body: str
    ) -> CoverLetterPDF:
        self._begin()
        self._letter_header(header)
        self._letter_body(body, signature=header.get("name", ""))
        return self

    def _letter_header(self, header: dict[str, str]) -> None:
        if header.get("name"):
            self.set_font("DejaVu", "B", 16)
            self._mc(8, header["name"], align="C")
            self.ln(2)
        if header.get("contact"):
            self.set_font("DejaVu", "", 9)
            self.set_text_color(100, 100, 100)
            self._mc(4.5, header["contact"], align="C")
            self.set_text_color(30, 30, 30)
            self.ln(8)
        if header.get("date"):
            self._date(header["date"])
        if header.get("recipient"):
            self.set_font("DejaVu", "", 10)
            for line in header["recipient"].split("\n"):
                self._mc(5, line)
            self.ln(4)

    def _letter_body(self, body: str, signature: str) -> None:
        blocks = [b.strip() for b in re.split(r"\n\s*\n", body.strip()) if b.strip()]
        if not blocks:
            if signature:
                self._signature(signature)
            return

        closing_idx: int | None = None
        for i, block in enumerate(blocks):
            if _is_closing_block(block):
                closing_idx = i

        body_blocks = blocks if closing_idx is None else blocks[:closing_idx]
        salutation_done = False
        for block in body_blocks:
            if not salutation_done and _is_salutation_block(block):
                self._salutation(block)
                salutation_done = True
                continue
            if _SUBJECT_RE.match(block):
                self._subject(block)
                continue
            self._paragraph(block)

        if closing_idx is not None:
            closing_lines = blocks[closing_idx].split("\n")
            keep = 1
            for j, line in enumerate(closing_lines):
                if _CLOSING_RE.match(line.strip()):
                    keep = j + 1
            self._closing("\n".join(closing_lines[:keep]))
        else:
            self.ln(8)
            self.set_font("DejaVu", "", 11)
            self._mc(6.5, "Sincerely,")
            self.ln(4)

        if signature:
            self._signature(signature)

    def _subject(self, text: str) -> None:
        self.set_font("DejaVu", "B", 11)
        self._mc(6.5, text)
        self.ln(4)

    def _date(self, text: str) -> None:
        self.set_font("DejaVu", "", 10)
        self.set_text_color(100, 100, 100)
        self._mc(5, text, align="L")
        self.set_text_color(30, 30, 30)
        self.ln(6)

    def _salutation(self, text: str) -> None:
        self.set_font("DejaVu", "", 11)
        self._mc(6.5, text)
        self.ln(5)

    def _paragraph(self, text: str) -> None:
        self.set_font("DejaVu", "", 11)
        self._mc(6.5, text, align="J")
        self.ln(4)

    def _closing(self, text: str) -> None:
        self.ln(8)
        self.set_font("DejaVu", "", 11)
        self._mc(6.5, text)
        self.ln(4)

    def _signature(self, text: str) -> None:
        self.set_font("DejaVu", "B", 11)
        self._mc(6.5, text)


class ResumePDF(_PDF):
    def render(self, text: str) -> ResumePDF:
        self._begin()
        lines = [l.rstrip("\r") for l in text.split("\n")]
        i = self._render_header(lines, 0)
        self._render_body(lines, i)
        return self

    def _render_header(self, lines: list[str], start: int) -> int:
        i = start
        n = len(lines)
        name_parts: list[str] = []
        contact_parts: list[str] = []
        headline_parts: list[str] = []
        phase = "name"

        while i < n:
            stripped = lines[i].strip()
            if not stripped:
                if phase == "name":
                    phase = "contact"
                else:
                    ahead = i + 1
                    while ahead < n and not lines[ahead].strip():
                        ahead += 1
                    if ahead < n and _is_section_header_line(lines[ahead].strip()):
                        break
                i += 1
                continue
            if _is_section_header_line(stripped):
                break
            if phase == "name":
                name_parts.append(stripped)
                phase = "contact"
            elif _is_headline(stripped):
                headline_parts.append(stripped)
            else:
                contact_parts.append(stripped)
            i += 1

        if name_parts:
            self.set_font("DejaVu", "B", 18)
            self._mc(10, " ".join(name_parts), align="C")
            self.ln(1)

        if contact_parts:
            self.set_font("DejaVu", "", 9)
            self.set_text_color(100, 100, 100)
            for line in contact_parts:
                self._mc(4.5, line, align="C")
            self.set_text_color(30, 30, 30)
            self.ln(4)

        if headline_parts:
            self.set_font("DejaVu", "B", 11)
            self._mc(6, " ".join(headline_parts), align="C")
            self.ln(6)

        return i

    def _render_body(self, lines: list[str], start: int) -> None:
        i = start
        n = len(lines)

        while i < n:
            stripped = lines[i].strip()
            if not stripped:
                i += 1
                continue
            if _DIVIDER_RE.match(stripped):
                i += 1
                continue
            if _is_section_header_line(stripped):
                self._section_header(stripped)
                i += 1
                if i < n and _DIVIDER_RE.match(lines[i].strip()):
                    i += 1
                continue
            if _is_job_entry(lines[i]):
                self._job_entry(lines[i])
                i += 1
                while i < n:
                    s = lines[i].strip()
                    if not s:
                        break
                    if _is_job_entry(lines[i]):
                        break
                    if _is_bullet(s):
                        self._bullet(s)
                        i += 1
                    else:
                        break
                self.ln(2)
                continue
            if _is_bullet(stripped):
                self._bullet(stripped)
                i += 1
                continue

            self._text_line(stripped)
            i += 1

    def _section_header(self, text: str) -> None:
        header = _clean_text(text.lstrip("#").strip().rstrip(":"))
        self.set_font("DejaVu", "B", 13)
        self.set_x(self.l_margin)
        w = self.get_string_width(header) + 6
        self.cell(w, 8, header)
        y = self.get_y()
        self.ln(10)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.5)
        self.line(self.MARGIN, y + 2, self.w - self.MARGIN, y + 2)
        self.set_line_width(0.2)
        self.ln(3)

    def _bullet(self, text: str) -> None:
        bullet_text = _BULLET_RE.sub("", text).strip()
        self.set_font("DejaVu", "", 10)
        indent = self.l_margin + 5
        marker = "•  "
        marker_w = self.get_string_width(marker)
        avail = self._bw - (indent - self.l_margin) - marker_w
        self.set_x(indent)
        self.cell(marker_w, 5.5, marker)
        self.set_x(indent + marker_w)
        self.multi_cell(avail, 5.5, bullet_text)

    def _job_entry(self, line: str) -> None:
        entry = _split_job_entry(_BULLET_RE.sub("", line.strip()).strip())
        title = " • ".join(
            part for part in (entry["title"], entry["company"]) if part
        )
        dates = entry["dates"]
        location = entry["location"]

        self.set_font("DejaVu", "B", 10)
        date_w = self.get_string_width(dates) + 2 if dates else 0
        title_w = self.get_string_width(title)

        if date_w and title_w < self._bw - date_w - 10:
            self.set_x(self.l_margin)
            self.cell(self._bw - date_w, 6, title)
            self.set_x(self.w - self.r_margin - date_w)
            self.cell(date_w, 6, dates, align="R")
        else:
            self._mc(5.5, title)
            if dates:
                self.set_font("DejaVu", "", 10)
                self.set_text_color(100, 100, 100)
                self._mc(5, dates, align="R")
                self.set_text_color(30, 30, 30)
        self.ln(1)

        if location:
            self.set_font("DejaVu", "", 9)
            self.set_text_color(100, 100, 100)
            self._mc(4.5, location)
            self.set_text_color(30, 30, 30)

    def _text_line(self, text: str) -> None:
        self.set_font("DejaVu", "", 10)
        self._mc(5.5, text)
