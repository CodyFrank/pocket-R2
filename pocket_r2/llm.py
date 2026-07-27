from __future__ import annotations
import unicodedata
import ollama


def generate_cover_letter(
    messages: list[dict],
    model: str = "",
    host: str | None = None,
) -> str:
    client = ollama.Client(host=host) if host else ollama.Client()
    response = client.chat(model=model, messages=messages)

    # std_text = unicodedata.normalize('NFKD', response["message"]["content"])
    # return std_text
    return response["message"]["content"]
