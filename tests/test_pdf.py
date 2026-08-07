from __future__ import annotations

import io

from pocket_r2.pdf import (
    CoverLetterPDF,
    ResumePDF,
    _clean_text,
    _is_job_entry,
    _is_section_header_line,
    _split_job_entry,
)


def test_clean_text_removes_markdown_and_tabs():
    assert _clean_text("**Bold** and tab\there") == "Bold and tab  here"


def test_section_header_not_job_line():
    assert _is_section_header_line("EXPERIENCE")
    assert not _is_section_header_line("Senior Engineer | Acme | Boston | 2020-Present")
    assert not _is_section_header_line("Greater Philadelphia | 908-338-4437")


def test_is_job_entry_bullet_prefixed():
    assert _is_job_entry("- Data Annotator | DataAnnotation | Remote | 03/2026-Present")
    assert _is_job_entry("Senior Engineer | Acme | 2020-Present")
    assert not _is_job_entry("- Built production systems")


def test_split_job_entry():
    entry = _split_job_entry("Data Annotator | DataAnnotation | Remote | 03/2026-Present")
    assert entry == {
        "title": "Data Annotator",
        "company": "DataAnnotation",
        "location": "Remote",
        "dates": "03/2026-Present",
    }


def test_resume_pdf_renders_markdown_smoke():
    text = (
        "**Jane Doe**\n"
        "Boston, MA | jane@example.com\n\n"
        "**EXPERIENCE**\n"
        "- Data Annotator | DataAnnotation | Remote | 03/2026-Present\n"
        "- Built production systems\n\n"
        "EDUCATION\n- Flatiron School | 04/2019-03/2020"
    )
    pdf = ResumePDF()
    pdf.render(text)
    out = pdf.output()
    assert isinstance(out, (bytes, bytearray))
    assert out.startswith(b"%PDF")
    assert len(out) > 1000


def test_cover_letter_with_header_smoke():
    header = {
        "name": "Jane Doe",
        "contact": "Boston, MA | jane@example.com",
        "date": "January 1, 2026",
        "recipient": "Hiring Manager\nAcme Corp",
    }
    body = "Dear Hiring Manager,\n\nI am excited.\n\nSincerely,"
    pdf = CoverLetterPDF()
    pdf.render_with_header(header, body)
    out = pdf.output()
    assert out.startswith(b"%PDF")


def test_cover_letter_plain_render_smoke():
    text = "Dear Hiring Team,\n\nBody text.\n\nSincerely,\nJane"
    pdf = CoverLetterPDF()
    pdf.render(text)
    out = pdf.output()
    assert out.startswith(b"%PDF")


def test_cover_letter_to_buffer():
    buf = io.BytesIO()
    header = {
        "name": "Jane Doe",
        "contact": "jane@example.com",
        "date": "January 1, 2026",
        "recipient": "Hiring Manager",
    }
    pdf = CoverLetterPDF()
    pdf.render_with_header(header, "Dear Hiring Manager,\n\nBody.\n\nSincerely,")
    pdf.output(buf)
    assert buf.getvalue().startswith(b"%PDF")
