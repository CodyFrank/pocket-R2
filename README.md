
# pocket-R2

AI cover letter and resume generator that runs entirely on local LLMs via Ollama.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) running locally with a model pulled:
  ```bash
  ollama pull qwen3-coder-next
  ```

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium   # required for JS-heavy job sites
```

## Usage

```bash
# Generate both cover letter and tailored resume
python -m pocket_r2 --url "https://..." --resume resume.txt

# From pasted text
python -m pocket_r2 --text "Software Engineer at Acme Corp..." --resume resume.txt

# Resume only (skip cover letter)
python -m pocket_r2 --url "https://..." --resume resume.txt --no-cover-letter

# Cover letter only (skip resume)
python -m pocket_r2 --url "https://..." --resume resume.txt --no-resume

# Print to terminal instead of saving PDFs
python -m pocket_r2 --url "https://..." --resume resume.txt --stdout

# Override model
python -m pocket_r2 --url "https://..." --resume resume.txt --model mistral
```

Cover letters and tailored resumes are saved as PDFs to the `output/` directory by default (configurable in `config.yaml`).

## SSRF Protection

By default, `--url` fetches are limited to public internet addresses. URLs that resolve to private/reserved IPs (localhost, RFC1918, link-local, cloud metadata like `169.254.169.254`) are refused, redirects are validated at each hop, and the Playwright browser blocks requests to non-public addresses. This prevents Server-Side Request Forgery against internal services.

Additional resource limits:
- DNS resolution has a 3-second timeout and fails closed (a host that can't be verified is refused).
- Responses larger than 2 MB are refused on both the static and Playwright fetch paths.

To allow fetching from private networks (unsafe), set `allow_private_urls: true` in `config.yaml` or pass `--allow-private-urls`. If a legitimate site is blocked, you can paste the posting text with `--text` instead.

## Prompt Injection Protection

Job postings, resumes, and skill lists are treated as data inputs by the prompt system. Generated output is additionally checked for injection:

- A deterministic check flags contact info/URLs that appear in the output but not in the resume, plus common injection phrasing.
- An LLM-based validator reviews the draft for fabricated facts, embedded instructions, and unauthorized content. If flagged, the document is regenerated once with a hardened prompt.
- If the regenerated draft is still flagged, a warning is printed but the output is saved so your workflow isn't blocked — review it before sending.

Disable the check with `--no-injection-check` or set `prompt_injection_check: false` in `config.yaml` (not recommended).

## API Keys & Privacy

By default `pocket-r2` uses your local Ollama model — no data ever leaves your machine. Cloud providers (OpenAI, Anthropic, Google, DeepSeek, Mistral) are supported, but only send data when you explicitly pass `--provider`.

API keys are stored **only on your machine** and are **never read from environment variables** (so they aren't exposed via `/proc/self/environ` or inherited by subprocesses like the Playwright browser):

- `pocket-r2 keys add openai` — prompts for the key (never echoed), stores it in your OS keyring (macOS Keychain, Windows Credential Locker, GNOME Keyring/KWallet)
- If no keyring is available (e.g. headless server), keys fall back to `~/.config/pocket-r2/credentials.yaml` with `0700`/`0600` permissions — the same posture as `~/.ssh/id_rsa`
- `pocket-r2 keys list` shows which providers have keys (never the values); `pocket-r2 keys status` shows the storage backend in use; `pocket-r2 keys remove <provider>` deletes a key

When you use a cloud provider, a warning is printed because the job posting and your resume are transmitted to that provider's servers. Ollama keeps everything local.

Note: keyring/0600-file storage protects against ambient environment readers and subprocess leakage. It does not protect against malware running as your user actively reading the file or keyring — the only complete protection for sensitive data is sticking with the local Ollama provider.

## Extra Skills

Create `skills.yaml` in the project root with skills not on your current resume:

```yaml
technical:
  - Kubernetes
  - Terraform
  - CI/CD pipelines
soft:
  - Team leadership
  - Cross-functional collaboration
certifications:
  - AWS Solutions Architect
```

These are injected into the LLM prompts to produce more tailored results.

## Configuration

Edit `config.yaml` to change defaults:

```yaml
model: qwen3-coder-next
ollama_host: http://localhost:11434
output_dir: output
resume_output_dir: output
skills_file: skills.yaml
pdf_page_size: Letter
allow_private_urls: false
prompt_injection_check: true
```

`pdf_page_size` accepts any fpdf2 format name (e.g. `Letter`, `A4`). Letter is the default since most posting sites target US employers.

Generated PDFs and your `resume.txt` are written with `0600` permissions so other local users can't read your personal data.

## Upload-Ready Output

Generated PDFs are cleaned before rendering so they are ready to upload without manual edits:

- The cover letter header (candidate name/contact from `resume.txt`, today's date, and a "Hiring Manager / <company>" recipient block) is auto-filled by the tool. The company name is best-effort (derived from the job URL or posting text); if it can't be determined, the recipient is just "Hiring Manager".
- Model output is normalized before rendering: preambles, trailing "Explanation"/"Notes" sections, markdown characters, placeholder tokens, and stray tabs/bullet characters are stripped.
- The format check (markdown, placeholders, preamble, trailing notes) is part of the prompt-injection validation loop, so drafts that violate the format are regenerated once automatically.

## License

MIT
