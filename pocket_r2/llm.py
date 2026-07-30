from __future__ import annotations

import os

_PROVIDER_CONFIGS: dict[str, tuple[str, str]] = {
    "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1"),
    "google": ("GOOGLE_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/"),
    "deepseek": ("DEEPSEEK_API_KEY", "https://api.deepseek.com"),
    "mistral": ("MISTRAL_API_KEY", "https://api.mistral.ai/v1"),
}


def generate(
    messages: list[dict],
    model: str = "",
    provider: str = "ollama",
    host: str | None = None,
) -> str:
    if provider == "ollama":
        return _generate_ollama(messages, model, host)
    elif provider == "anthropic":
        return _generate_anthropic(messages, model)
    elif provider in _PROVIDER_CONFIGS:
        return _generate_openai_compatible(messages, model, provider)
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


def _generate_openai_compatible(
    messages: list[dict],
    model: str,
    provider: str,
) -> str:
    from openai import OpenAI

    env_var, base_url = _PROVIDER_CONFIGS[provider]
    api_key = os.environ.get(env_var)
    if not api_key:
        raise ValueError(f"{env_var} environment variable is not set")
    client = OpenAI(api_key=api_key, base_url=base_url)
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
