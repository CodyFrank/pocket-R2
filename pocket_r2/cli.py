from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml
from fpdf import FPDF

from pocket_r2.llm import generate_cover_letter
from pocket_r2.prompts import build_messages
from pocket_r2.scraper import get_job_text

DEFAULT_CONFIG_PATH = Path("config.yaml")
DEFAULT_RESUME_PATH = Path("resume.txt")


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pocket-r2",
        description="Generate a cover letter from a job posting using a local LLM.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="URL of the job posting")
    source.add_argument("--text", help="Raw text of the job posting")

    parser.add_argument(
        "--resume", type=Path, default=DEFAULT_RESUME_PATH,
        help="Path to resume file (default: ./resume.txt)",
    )
    parser.add_argument(
        "--model", default=None,
        help="Ollama model to use (overrides config.yaml)",
    )
    parser.add_argument(
        "--stdout", action="store_true",
        help="Print cover letter to terminal instead of saving PDF",
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG_PATH,
        help="Path to config file (default: ./config.yaml)",
    )
    return parser.parse_args(argv)


def save_as_pdf(text: str, output_dir: Path) -> Path:
    """Save cover letter text as a PDF. Returns the path to the saved file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cover_letter_{timestamp}.pdf"
    filepath = output_dir / filename

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.set_font("Helvetica", size=11)

    # pdf.multi_cell(w=0, h=10, txt=text)

    safe = text.encode("latin-1", errors="replace").decode("latin-1")
    # for line in safe.split("\n"):
    pdf.multi_cell(0, 7, safe)

    pdf.output(str(filepath))
    return filepath


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config = load_config(args.config)

    model = args.model or config.get("model", "qwen3-coder-next")
    host = config.get("ollama_host")
    output_dir = Path(config.get("output_dir", "output"))

    if not args.resume.exists():
        print(f"Resume file not found: {args.resume}", file=sys.stderr)
        raise SystemExit(1)

    job_text = get_job_text(url=args.url, text=args.text)
    resume_text = args.resume.read_text().strip()

    print(f"Using model: {model}", file=sys.stderr)
    messages = build_messages(job_text, resume_text)

    print("Generating cover letter...", file=sys.stderr)
    cover_letter = generate_cover_letter(messages, model=model, host=host)

    if args.stdout:
        print(cover_letter)
    else:
        filepath = save_as_pdf(cover_letter, output_dir)
        print(f"Saved to {filepath}", file=sys.stderr)


if __name__ == "__main__":
    main()
