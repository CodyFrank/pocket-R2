from __future__ import annotations

from pocket_r2.normalize import (
    build_letter_header,
    compose_cover_letter,
    detect_company,
    fix_tabs,
    normalize_bullets,
    normalize_cover_body,
    normalize_resume,
    parse_contact_from_resume,
    replace_placeholders,
    strip_letter_header,
    strip_markdown,
    strip_preamble,
    strip_trailing_notes,
)


def test_strip_markdown_removes_artifacts():
    text = "**TECHNICAL SKILLS**\n---\n- **Python** & `code`\n# Heading\n### Other"
    result = strip_markdown(text)
    assert "**" not in result
    assert "#" not in result
    assert "`" not in result
    assert result.strip().startswith("TECHNICAL SKILLS")
    assert "\n- Python" in result


def test_normalize_bullets_maps_to_dash():
    text = "• one\n▪ two\n→ three\n1. four\n2) five\n- six"
    result = normalize_bullets(text)
    lines = result.split("\n")
    assert all(line.startswith("- ") for line in lines)
    assert lines[0] == "- one"


def test_fix_tabs():
    assert fix_tabs("Remote\t07/2020-04/2026") == "Remote  07/2020-04/2026"


def test_strip_preamble_cover():
    text = (
        "Okay, here's a cover letter drafted based on the job posting.\n\n"
        "Dear Hiring Manager,\n\nBody.\n\nSincerely,\n"
    )
    result = strip_preamble(text, "cover")
    assert result.startswith("Dear Hiring Manager,")


def test_strip_preamble_clean_passthrough():
    text = "Dear Hiring Manager,\n\nBody."
    assert strip_preamble(text, "cover") == text


def test_strip_trailing_notes_cover():
    text = (
        "Dear Hiring Manager,\n\nBody.\n\nSincerely,\n\n"
        "Explanation of Choices & Rationale:\n1. Tone is professional."
    )
    result = strip_trailing_notes(text, "cover")
    assert "Explanation" not in result
    assert "Sincerely," in result


def test_strip_trailing_notes_resume():
    text = (
        "TECHNICAL SKILLS\n- Python\n\nEDUCATION\n- School\n\n"
        "*Note:** I've significantly enhanced the language to match."
    )
    result = strip_trailing_notes(text, "resume")
    assert "Note" not in result
    assert "- Python" in result


def test_replace_placeholders():
    contact = {
        "name": "Jane Doe",
        "phone": "555-123-4567",
        "email": "jane@example.com",
        "location": "Boston, MA",
    }
    text = "[Your Name]\n[Your Phone Number] | [Your Email Address] | [Date]"
    result = replace_placeholders(text, contact)
    assert "Jane Doe" in result
    assert "555-123-4567" in result
    assert "jane@example.com" in result


def test_replace_placeholders_drops_unknown_with_no_value():
    contact = {"name": "Jane Doe", "phone": "", "email": "", "location": ""}
    result = replace_placeholders("[Your Address]\n[Your Name]", contact)
    assert "[Your Address]" not in result
    assert result.strip() == "Jane Doe"


def test_strip_letter_header():
    body = (
        "Cody Frank\n[Your Address]\n[Your Phone Number]\n[Your Email Address]\n\n"
        "[Date]\n\nHiring Manager\nStellic\n\n"
        "Subject: Senior Software Engineer\n\n"
        "Dear Hiring Manager,\n\nBody.\n\nSincerely,"
    )
    result = strip_letter_header(body)
    assert result.startswith("Subject: Senior Software Engineer")
    assert "Cody Frank" not in result.split("Subject:")[0]
    assert "Stellic" not in result.split("Subject:")[0]


def test_parse_contact_from_resume():
    resume = (
        "Jane Doe\n"
        "Boston, MA | 555-123-4567 | jane@example.com | GitHub | LinkedIn\n\n"
        "EXPERIENCE\n- Worked on things"
    )
    contact = parse_contact_from_resume(resume)
    assert contact["name"] == "Jane Doe"
    assert contact["phone"] == "555-123-4567"
    assert contact["email"] == "jane@example.com"
    assert contact["location"] == "Boston, MA"


def test_detect_company_from_url():
    assert (
        detect_company(None, "https://www.stellic.com/careers/engineer") == "Stellic"
    )


def test_detect_company_from_text():
    assert (
        detect_company("Stellic is hiring a Senior Software Engineer", None)
        == "Stellic"
    )


def test_detect_company_unknown():
    assert detect_company(None, "https://jobs.lever.co/1234") is None


def test_build_letter_header_and_compose():
    contact = parse_contact_from_resume(
        "Jane Doe\nBoston, MA | 555-123-4567 | jane@example.com"
    )
    header = build_letter_header(contact, "Acme Corp", today="January 1, 2026")
    assert header["recipient"] == "Hiring Manager\nAcme Corp"
    letter = compose_cover_letter(
        header, "Dear Hiring Manager,\n\nBody.\n\nSincerely,"
    )
    assert letter.startswith("Jane Doe")
    assert "January 1, 2026" in letter
    assert "Acme Corp" in letter
    assert letter.endswith("Jane Doe")


def test_compose_drops_trailing_signature_from_body():
    header = build_letter_header(
        {"name": "Jane Doe", "location": "", "phone": "", "email": "", "urls": ""},
        today="January 1, 2026",
    )
    letter = compose_cover_letter(
        header, "Dear Hiring Manager,\n\nBody.\n\nSincerely,\nJane Doe"
    )
    assert letter.endswith("Jane Doe")
    assert letter.count("Jane Doe") == 2  # header + signature only


def test_normalize_resume_end_to_end():
    dirty = (
        "Here is your tailored resume.\n\n"
        "**Jane Doe**\n"
        "Boston, MA | jane@example.com\n\n"
        "**EXPERIENCE**\n"
        "• Senior Engineer | Acme | Boston | 2020-Present\n"
        "• Built things\n\n"
        "*Note:** I've significantly rewritten this for the role."
    )
    result = normalize_resume(dirty)
    assert "Here is your tailored resume" not in result
    assert "**" not in result
    assert "Note" not in result
    assert result.startswith("Jane Doe")
    assert "Senior Engineer | Acme | Boston | 2020-Present" in result
    assert "- Built things" in result


def test_normalize_cover_body_end_to_end():
    contact = parse_contact_from_resume(
        "Cody Frank\nGreater Philadelphia | 908-338-4437 | cody.frank30@gmail.com"
    )
    dirty = (
        "Okay, here's a cover letter incorporating the analysis we performed.\n\n"
        "Cody Frank\n[Your Address]\n908-338-4437\ncody.frank30@gmail.com\n\n"
        "[Date]\n\nHiring Manager\nStellic\n\n"
        "**Subject: Senior Software Engineer**\n\n"
        "Dear Hiring Manager,\n\nI am excited about this role.\n\nSincerely,\n\n"
        "---\n**Explanation of Choices & Rationale:**\n1. Tone."
    )
    result = normalize_cover_body(dirty, contact, "Stellic")
    assert result.startswith("Subject: Senior Software Engineer")
    assert "Okay, here's" not in result
    assert "Explanation" not in result
    assert "Sincerely," in result
    assert "Cody Frank" not in result.split("Dear")[0]


def test_normalize_strips_single_asterisks():
    result = normalize_resume("- *AuditBull** | Serverless | 2020")
    assert "*" not in result
    assert result.startswith("- AuditBull | Serverless | 2020")
