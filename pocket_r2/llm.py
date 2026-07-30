from __future__ import annotations

import os


def generate(
    messages: list[dict],
    model: str = "",
    provider: str = "ollama",
    host: str | None = None,
) -> str:
    if provider == "ollama":
        return _generate_ollama(messages, model, host)
    elif provider == "openai":
        return _generate_openai(messages, model)
    elif provider == "anthropic":
        return _generate_anthropic(messages, model)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _generate_ollama(
    messages: list[dict],
    model: str,
    host: str | None,
) -> str:
    import ollama

    client = ollama.Client(host=host) if host else ollama.Client()
    response = client.chat(model=model, messages=messages)
    return response["message"]["content"]


def _generate_openai(
    messages: list[dict],
    model: str,
) -> str:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set"
        )
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content


def _generate_anthropic(
    messages: list[dict],
    model: str,
) -> str:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is not set"
        )

    system_content = None
    api_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"]
        else:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

    client = anthropic.Anthropic(api_key=api_key)
    kwargs: dict = {
        "model": model,
        "max_tokens": 4096,
        "messages": api_messages,
    }
    if system_content:
        kwargs["system"] = system_content

    response = client.messages.create(**kwargs)
    return response.content[0].text
