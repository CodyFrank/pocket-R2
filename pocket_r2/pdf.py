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
    if not s or len(s) > 55:
        return False
    if _MARKDOWN_HEADER_RE.match(s):
        return True
    if s.isupper() and len(s.split()) <= 5:
        return True
    if s.lower().rstrip(":").strip() in _SECTION_KEYWORDS:
        return True
    return False


def _is_bullet(line: str) -> bool:
    return bool(_BULLET_RE.match(line.strip()))


def _is_job_entry(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if "|" in s:
        parts = [p.strip() for p in s.split("|")]
        if len(parts) >= 2:
            return True
    if _JOB_DATE_RE.search(s):
        return True
    return False


class _PDF(FPDF):
    MARGIN = 25

    def __init__(self) -> None:
        super().__init__()
        self.add_font("DejaVu", "", str(FONT_DIR / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"))
        self.set_auto_page_break(auto=True, margin=self.MARGIN)

    @property
    def _bw(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def _mc(self, h: float, text: str, align: str = "L") -> None:
        self.set_x(self.l_margin)
        self.multi_cell(self._bw, h, text, align=align)

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

    def _date(self, text: str) -> None:
        self.set_font("DejaVu", "", 10)
        self.set_text_color(100, 100, 100)
        self._mc(5, text, align="R")
        self.set_text_color(30, 30, 30)
        self.ln(8)

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
        self.set_font("DejaVu", "", 11)
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
            if _is_bullet(stripped):
                self._bullet(stripped)
                i += 1
                continue
            if _is_job_entry(lines[i]):
                self._job_title(lines[i])
                i += 1
                while i < n:
                    s = lines[i].strip()
                    if not s:
                        break
                    if _is_bullet(s):
                        self._bullet(s)
                        i += 1
                    else:
                        break
                self.ln(2)
                continue

            self._text_line(stripped)
            i += 1

    def _section_header(self, text: str) -> None:
        self.set_font("DejaVu", "B", 13)
        self.set_x(self.l_margin)
        header = text.lstrip("#").strip().rstrip(":")
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
        self.set_x(indent)
        self.multi_cell(self.w - self.r_margin - indent, 5.5, "•  " + bullet_text)

    def _job_title(self, text: str) -> None:
        self.set_font("DejaVu", "B", 10)
        self._mc(5.5, text.strip())
        self.ln(1)

    def _text_line(self, text: str) -> None:
        self.set_font("DejaVu", "", 10)
        self._mc(5.5, text)
