from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml

from pocket_r2.llm import generate
from pocket_r2.pdf import CoverLetterPDF, ResumePDF
from pocket_r2.prompts import build_cover_letter_messages, build_resume_messages
from pocket_r2.scraper import get_job_text

DEFAULT_CONFIG_PATH = Path("config.yaml")
DEFAULT_RESUME_PATH = Path("resume.txt")


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_skills(path: Path) -> str | None:
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    lines = []
    for category, items in data.items():
        if items:
            lines.append(f"### {category.replace('_', ' ').title()}")
            lines.extend(f"- {item}" for item in items)
            lines.append("")
    text = "\n".join(lines).strip()
    return text if text else None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pocket-r2",
        description="Generate a cover letter and/or tailored resume from a job posting using a local LLM.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="URL of the job posting")
    source.add_argument("--text", help="Raw text of the job posting")

    parser.add_argument(
        "--resume",
        type=Path,
        default=DEFAULT_RESUME_PATH,
        help="Path to resume file (default: ./resume.txt)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Ollama model to use (overrides config.yaml)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print output to terminal instead of saving PDFs",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to config file (default: ./config.yaml)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Skip resume tailoring",
    )
    parser.add_argument(
        "--no-cover-letter",
        action="store_true",
        help="Skip cover letter generation",
    )
    return parser.parse_args(argv)


def _timestamped_path(output_dir: Path, prefix: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"{prefix}_{ts}.pdf"


def save_cover_letter_pdf(text: str, output_dir: Path) -> Path:
    filepath = _timestamped_path(output_dir, "cover_letter")
    pdf = CoverLetterPDF()
    pdf.render(text)
    pdf.output(str(filepath))
    return filepath


def save_resume_pdf(text: str, output_dir: Path) -> Path:
    filepath = _timestamped_path(output_dir, "resume")
    pdf = ResumePDF()
    pdf.render(text)
    pdf.output(str(filepath))
    return filepath


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config = load_config(args.config)

    if args.no_resume and args.no_cover_letter:
        print(
            "Both --no-resume and --no-cover-letter set — nothing to generate.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    model = args.model or config.get("model", "qwen3-coder-next")
    host = config.get("ollama_host")
    output_dir = Path(config.get("output_dir", "output"))
    resume_output_dir = Path(config.get("resume_output_dir", "output"))
    skills_file = Path(config.get("skills_file", "skills.yaml"))

    if not args.resume.exists():
        print(f"Resume file not found: {args.resume}", file=sys.stderr)
        raise SystemExit(1)

    job_text = get_job_text(url=args.url, text=args.text)
    resume_text = args.resume.read_text().strip()
    skills_text = load_skills(skills_file)

    if skills_text:
        print(f"Loaded skills from {skills_file}", file=sys.stderr)

    print(f"Using model: {model}", file=sys.stderr)

    if not args.no_cover_letter:
        print("Generating cover letter...", file=sys.stderr)
        cover_messages = build_cover_letter_messages(job_text, resume_text, skills_text)
        cover_letter = generate(cover_messages, model=model, host=host)

        if args.stdout:
            print("--- Cover Letter ---")
            print(cover_letter)
            print()
        else:
            filepath = save_cover_letter_pdf(cover_letter, output_dir)
            print(f"Cover letter saved to {filepath}", file=sys.stderr)

    if not args.no_resume:
        print("Generating tailored resume...", file=sys.stderr)
        resume_messages = build_resume_messages(job_text, resume_text, skills_text)
        tailored_resume = generate(resume_messages, model=model, host=host)

        if args.stdout:
            print("--- Tailored Resume ---")
            print(tailored_resume)
        else:
            filepath = save_resume_pdf(tailored_resume, resume_output_dir)
            print(f"Tailored resume saved to {filepath}", file=sys.stderr)


if __name__ == "__main__":
    main()
