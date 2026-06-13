from __future__ import annotations

import os
import json
from typing import Any

try:
    import openai
except Exception:
    openai = None

try:
    import google.generativeai as genai
except Exception:
    genai = None


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()  # 'google' or 'openai'
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-mini")


def _has_openai() -> bool:
    return bool(OPENAI_KEY and openai)


def _has_google() -> bool:
    return bool(GOOGLE_KEY and genai)


def _has_llm() -> bool:
    if LLM_PROVIDER == "google":
        return _has_google()
    if LLM_PROVIDER == "openai":
        return _has_openai()
    # autodetect preference: prefer Google then OpenAI
    return _has_google() or _has_openai()


def _call_openai_chat(messages: list[dict], model: str, temperature: float = 0.0, max_tokens: int = 300) -> str:
    resp = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
    return resp.choices[0].message.content


def _call_google_chat(messages: list[dict], model: str, temperature: float = 0.0, max_tokens: int = 300) -> str:
    # google.generativeai chat API may vary between versions; we attempt a best-effort call
    genai.configure(api_key=GOOGLE_KEY)
    try:
        # prefer chat.create if available
        chat_resp = genai.chat.create(model=model, messages=messages)
        # the exact field with text can vary; try common locations
        if hasattr(chat_resp, "candidates") and chat_resp.candidates:
            return chat_resp.candidates[0].content
        if hasattr(chat_resp, "content"):
            return chat_resp.content
        return str(chat_resp)
    except Exception:
        # fallback: try a generic create if API differs
        resp = genai.create(model=model, prompt="\n".join(m["content"] for m in messages))
        return getattr(resp, "content", str(resp))


def plan_tools(message: str, provider: str | None = None, api_key: str | None = None) -> list[tuple[str, dict[str, Any]]]:
    """Ask an LLM to plan which MCP tools to call for the given message.

    Returns a list of (tool_name, arguments) tuples. If the LLM is not
    configured, returns an empty list.
    """
    # allow per-call overrides
    call_provider = (provider or LLM_PROVIDER or "").strip().lower()
    call_api_key = api_key

    if call_provider == "google":
        has_llm = bool((call_api_key or GOOGLE_KEY) and genai)
    elif call_provider == "openai":
        has_llm = bool((call_api_key or OPENAI_KEY) and openai)
    else:
        # autodetect
        has_llm = _has_llm()

    if not has_llm:
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
        if call_provider == "google" or (not call_provider and _has_google()):
            # configure google API key if provided
            if call_api_key:
                genai.configure(api_key=call_api_key)
            content = _call_google_chat(messages, model=GOOGLE_MODEL, temperature=0.0, max_tokens=300)
        elif call_provider == "openai" or (not call_provider and _has_openai()):
            if call_api_key:
                openai.api_key = call_api_key
            content = _call_openai_chat(messages, model=OPENAI_MODEL, temperature=0.0, max_tokens=300)
        else:
            return []

        data = json.loads(content)
        out: list[tuple[str, dict[str, Any]]] = []
        for item in data:
            tool = item.get("tool")
            args = item.get("arguments", {}) or {}
            if isinstance(tool, str) and isinstance(args, dict):
                out.append((tool, args))
        return out
    except Exception:
        return []


def generate_answer(message: str, results: dict[str, Any], provider: str | None = None, api_key: str | None = None) -> str:
    """Ask the LLM to synthesize a natural-language answer from tool results.

    If LLM is not configured, returns an empty string.
    """
    call_provider = (provider or LLM_PROVIDER or "").strip().lower()
    call_api_key = api_key

    if call_provider == "google":
        has_llm = bool((call_api_key or GOOGLE_KEY) and genai)
    elif call_provider == "openai":
        has_llm = bool((call_api_key or OPENAI_KEY) and openai)
    else:
        has_llm = _has_llm()

    if not has_llm:
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
        if call_provider == "google" or (not call_provider and _has_google()):
            if call_api_key:
                genai.configure(api_key=call_api_key)
            return _call_google_chat(messages, model=GOOGLE_MODEL, temperature=0.2, max_tokens=400).strip()
        if call_provider == "openai" or (not call_provider and _has_openai()):
            if call_api_key:
                openai.api_key = call_api_key
            return _call_openai_chat(messages, model=OPENAI_MODEL, temperature=0.2, max_tokens=400).strip()
    except Exception:
        return ""

    return ""
