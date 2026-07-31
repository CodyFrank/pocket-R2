
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

To allow fetching from private networks (unsafe), set `allow_private_urls: true` in `config.yaml` or pass `--allow-private-urls`. If a legitimate site is blocked, you can paste the posting text with `--text` instead.

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
```

## License

MIT
