
# pocket-R2

AI cover letter generator that runs entirely on local LLMs via Ollama.

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
# From a job posting URL
python -m pocket_r2 --url "https://..." --resume resume.txt

# From pasted text
python -m pocket_r2 --text "Software Engineer at Acme Corp..." --resume resume.txt

# Print to terminal instead of saving PDF
python -m pocket_r2 --url "https://..." --resume resume.txt --stdout

# Override model
python -m pocket_r2 --url "https://..." --resume resume.txt --model mistral
```

Cover letters are saved as PDFs to the `output/` directory by default (configurable in `config.yaml`).

## Configuration

Edit `config.yaml` to change defaults:

```yaml
model: qwen3-coder-next
ollama_host: http://localhost:11434
output_dir: output
```

## License

MIT
