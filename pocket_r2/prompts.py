SYSTEM_PROMPT = """\
You are a professional cover letter writer. Given a job posting and a candidate's \
resume, write a tailored cover letter that:

- Addresses the specific role and company
- Highlights directly relevant experience from the resume
- Matches the tone and language of the job posting
- Is concise (250-400 words)
- Avoids generic filler phrases
- Does not repeat the resume verbatim
"""

USER_PROMPT = """\
## Job Posting

{job_text}

## Candidate Resume

{resume_text}

Write a cover letter for this position.\
"""


def build_messages(job_text: str, resume_text: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT.format(
            job_text=job_text,
            resume_text=resume_text,
        )},
    ]
