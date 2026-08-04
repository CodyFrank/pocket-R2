from __future__ import annotations

import stat

from pocket_r2.cli import save_cover_letter_pdf, save_resume_pdf


def _is_0600(path) -> bool:
    return stat.S_IMODE(path.stat().st_mode) == 0o600


def test_cover_letter_pdf_0600(tmp_path):
    text = "Dear Hiring Team,\n\nBody text.\n\nSincerely,\nJane"
    path = save_cover_letter_pdf(text, tmp_path)
    assert path.exists()
    assert _is_0600(path)


def test_resume_pdf_0600(tmp_path):
    text = "Jane Doe\njane@example.com\n\nExperience\n- built things"
    path = save_resume_pdf(text, tmp_path)
    assert path.exists()
    assert _is_0600(path)
