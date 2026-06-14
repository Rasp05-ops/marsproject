from __future__ import annotations

import os
import json
import logging
import re
import warnings
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

try:
    import openai
except Exception:
    openai = None

try:
    from google import genai
except Exception:
    genai = None

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as legacy_genai
except Exception:
    legacy_genai = None


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()  # 'google' or 'openai'
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-3.1-flash-lite")

logger = logging.getLogger(__name__)
_last_error: str | None = None


def _remember_error(context: str, exc: Exception) -> None:
    global _last_error
    _last_error = f"{context}: {exc}"
    logger.warning("LLM %s failed: %s", context, exc)


def _has_openai(api_key: str | None = None) -> bool:
    return bool((api_key or OPENAI_KEY) and openai)


def _has_google(api_key: str | None = None) -> bool:
    return bool((api_key or GOOGLE_KEY) and (genai or legacy_genai))


def _has_llm(api_key: str | None = None) -> bool:
    if LLM_PROVIDER == "google":
        return _has_google(api_key)
    if LLM_PROVIDER == "openai":
        return _has_openai(api_key)
    # autodetect preference: prefer Google then OpenAI
    return _has_google(api_key) or _has_openai(api_key)


def _provider_available(provider: str, api_key: str | None = None) -> bool:
    if provider == "google":
        return _has_google(api_key)
    if provider == "openai":
        return _has_openai(api_key)
    return _has_llm(api_key)


def _chosen_provider(provider: str | None = None, api_key: str | None = None) -> str:
    requested = (provider or LLM_PROVIDER or "").strip().lower()
    if requested:
        return requested
    if _has_google(api_key):
        return "google"
    if _has_openai(api_key):
        return "openai"
    return ""


def _call_openai_chat(messages: list[dict], model: str, temperature: float = 0.0, max_tokens: int = 300, api_key: str | None = None) -> str:
    client = openai.OpenAI(api_key=api_key or OPENAI_KEY)
    resp = client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
    return resp.choices[0].message.content or ""


def _call_google_chat(messages: list[dict], model: str, temperature: float = 0.0, max_tokens: int = 300, api_key: str | None = None) -> str:
    prompt_parts = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        prompt_parts.append(f"Instructions: {content}" if role == "system" else content)
    prompt = "\n\n".join(prompt_parts)

    if genai:
        client = genai.Client(api_key=api_key or GOOGLE_KEY)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        return getattr(response, "text", "") or ""

    legacy_genai.configure(api_key=api_key or GOOGLE_KEY)
    gmodel = legacy_genai.GenerativeModel(model)
    response = gmodel.generate_content(
        prompt,
        generation_config=legacy_genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return getattr(response, "text", "") or ""


def _parse_json_array(content: str) -> list[Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\[[\s\S]*\]", cleaned)
    return json.loads(match.group(0) if match else cleaned)


def status(provider: str | None = None, api_key: str | None = None) -> dict[str, Any]:
    chosen = _chosen_provider(provider, api_key)
    requested = (provider or LLM_PROVIDER or "").strip().lower()
    configured = bool(chosen and _provider_available(chosen, api_key))
    reason = ""
    if not configured:
        if requested == "google" and not (genai or legacy_genai):
            reason = "google-genai is not installed"
        elif requested == "openai" and not openai:
            reason = "openai is not installed"
        elif requested:
            reason = f"missing API key for {requested}"
        else:
            reason = "missing GOOGLE_API_KEY or OPENAI_API_KEY"
    return {
        "provider": chosen or requested or "none",
        "configured": configured,
        "mode": "llm" if configured else "fallback",
        "reason": reason,
        "last_error": _last_error,
    }


def plan_tools(message: str, provider: str | None = None, api_key: str | None = None) -> list[tuple[str, dict[str, Any]]]:
    """Ask an LLM to plan which MCP tools to call for the given message.

    Returns a list of (tool_name, arguments) tuples. If the LLM is not
    configured, returns an empty list.
    """
    # allow per-call overrides
    call_provider = _chosen_provider(provider, api_key)
    call_api_key = api_key

    if not _provider_available(call_provider, call_api_key):
        return []

    system = (
        "You are a planner that receives a user's natural language query and must return"
        " a JSON array of tool calls. Each entry must be an object with the keys 'tool'"
        " (string) and 'arguments' (object). The 'tool' values must match available"
        " MCP tool names such as 'library.search_books', 'cafeteria.get_menu',"
        " 'events.list_events', 'academics.summary', 'academics.low_attendance',"
        " or 'notices.list_notices'. Keep the list minimal and only include tools that"
        " are directly useful. Example response:\n[{\n  \"tool\": \"library.search_books\",\n  \"arguments\": {\"query\": \"ai\"}\n}]"
    )

    messages = [{"role": "system", "content": system}, {"role": "user", "content": message}]

    try:
        if call_provider == "google":
            content = _call_google_chat(messages, model=GOOGLE_MODEL, temperature=0.0, max_tokens=300, api_key=call_api_key)
        elif call_provider == "openai":
            content = _call_openai_chat(messages, model=OPENAI_MODEL, temperature=0.0, max_tokens=300, api_key=call_api_key)
        else:
            return []

        data = _parse_json_array(content)
        out: list[tuple[str, dict[str, Any]]] = []
        for item in data:
            tool = item.get("tool")
            args = item.get("arguments", {}) or {}
            if isinstance(tool, str) and isinstance(args, dict):
                out.append((tool, args))
        return out
    except Exception as exc:
        _remember_error("tool planning", exc)
        return []


def generate_answer(message: str, results: dict[str, Any], provider: str | None = None, api_key: str | None = None) -> str:
    """Ask the LLM to synthesize a natural-language answer from tool results.

    If LLM is not configured, returns an empty string.
    """
    call_provider = _chosen_provider(provider, api_key)
    call_api_key = api_key

    if not _provider_available(call_provider, call_api_key):
        return ""

    system = (
        "You are a helpful campus assistant that composes a concise answer to the user's"
        " question. Use the provided tool results to produce a short, factual reply. If"
        " the results are insufficient, say you couldn't find more details. Return plain text."
    )

    tools_summary = json.dumps(results, default=str)
    prompt = f"User question: {message}\n\nTool results: {tools_summary}\n\nAnswer:"
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]

    try:
        if call_provider == "google":
            return _call_google_chat(messages, model=GOOGLE_MODEL, temperature=0.2, max_tokens=400, api_key=call_api_key).strip()
        if call_provider == "openai":
            return _call_openai_chat(messages, model=OPENAI_MODEL, temperature=0.2, max_tokens=400, api_key=call_api_key).strip()
    except Exception as exc:
        _remember_error("answer generation", exc)
        return ""

    return ""
