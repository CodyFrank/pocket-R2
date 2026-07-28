from __future__ import annotations

import ollama


def generate(
    messages: list[dict],
    model: str = "",
    host: str | None = None,
) -> str:
    client = ollama.Client(host=host) if host else ollama.Client()
    response = client.chat(model=model, messages=messages)
    return response["message"]["content"]
