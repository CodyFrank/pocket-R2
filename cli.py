from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

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
        "--output", type=Path, default=None,
        help="Save cover letter to file instead of printing",
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG_PATH,
        help="Path to config file (default: ./config.yaml)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config = load_config(args.config)

    model = args.model or config.get("model", "hemanth/coverletter")
    host = config.get("ollama_host")

    if not args.resume.exists():
        print(f"Resume file not found: {args.resume}", file=sys.stderr)
        raise SystemExit(1)

    job_text = get_job_text(url=args.url, text=args.text)
    resume_text = args.resume.read_text().strip()

    print(f"Using model: {model}", file=sys.stderr)
    messages = build_messages(job_text, resume_text)

    print("Generating cover letter...", file=sys.stderr)
    cover_letter = generate_cover_letter(messages, model=model, host=host)

    if args.output:
        args.output.write_text(cover_letter)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(cover_letter)


if __name__ == "__main__":
    main()
