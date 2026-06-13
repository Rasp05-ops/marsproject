from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.data import CAFETERIA_TIMINGS, COURSES, EVENTS, LIBRARY_BOOKS, MENU, NOTICES, PROFILE
from app.mcp_servers import SERVERS
from app.mcp_servers.academics import academics_server
from app.mcp_servers.cafeteria import cafeteria_server
from app.mcp_servers.events import events_server
from app.mcp_servers.library import library_server
from app.mcp_servers.notices import notices_server
from app.models import (
    AssistantRequest,
    AssistantResponse,
    Book,
    Course,
    Event,
    McpToolCall,
    McpToolResult,
    MenuResponse,
    Notice,
)
from app.services.assistant import run_assistant
import httpx
import time

def _http_request_with_retries(method: str, url: str, /, retries: int = 3, backoff: float = 0.5, **kwargs):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            resp = httpx.request(method, url, timeout=10.0, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as exc:
            last_exc = exc
            if attempt == retries:
                raise
            time.sleep(backoff * (2 ** (attempt - 1)))
    raise last_exc
import httpx

USE_MICROSERVICES = os.getenv("USE_MICROSERVICES", "false").lower() in ("1", "true", "yes")
MCP_BASES = {
    "library": os.getenv("MCP_LIBRARY_URL", "http://mcp_library:8001"),
    "cafeteria": os.getenv("MCP_CAFETERIA_URL", "http://mcp_cafeteria:8002"),
    "events": os.getenv("MCP_EVENTS_URL", "http://mcp_events:8003"),
    "academics": os.getenv("MCP_ACADEMICS_URL", "http://mcp_academics:8004"),
    "notices": os.getenv("MCP_NOTICES_URL", "http://mcp_notices:8005"),
}

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "CampusIQ Backend"),
    description="Unified campus intelligence backend with independent MCP-style data servers.",
    version="0.1.0",
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "campus-iq-backend"}


@app.get("/api/debug/llm")
def debug_llm() -> dict[str, Any]:
    """Temporary endpoint to diagnose LLM connectivity."""
    import traceback
    info: dict[str, Any] = {}
    google_key = os.getenv("GOOGLE_API_KEY", "")
    info["google_key_set"] = bool(google_key)
    info["google_key_prefix"] = google_key[:8] + "..." if google_key else ""
    try:
        import google.generativeai as genai
        info["genai_imported"] = True
        genai.configure(api_key=google_key)
        
        # List available models to help user find the right one
        try:
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            info["available_models"] = models
        except Exception as e:
            info["list_models_error"] = str(e)

        model_name = "gemini-2.0-flash"
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content("Say hello in one word.")
        info["target_model"] = model_name
        info["response"] = resp.text
        info["status"] = "SUCCESS"
    except Exception as e:
        info["genai_imported"] = True
        info["status"] = "FAILED"
        info["error"] = str(e)
        info["traceback"] = traceback.format_exc()
    return info


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    academics = academics_server.summary()
    return {
        "profile": PROFILE,
        "stats": {
            "books_borrowed": len([book for book in LIBRARY_BOOKS if book["status"] == "borrowed"]),
            "events_this_week": len(EVENTS),
            "average_attendance": academics["average_attendance"],
            "pending_notices": len([notice for notice in NOTICES if notice["urgent"]]),
        },
        "library": library_server.stats(),
        "lunch": cafeteria_server.get_menu("lunch"),
        "upcoming_events": events_server.list_events(limit=3),
        "recent_notices": notices_server.list_notices(limit=4),
        "academics": academics,
    }


@app.get("/api/library/books", response_model=list[Book])
def list_books(
    query: str | None = Query(default=None),
    status: str | None = Query(default=None, pattern="^(available|borrowed|reserved)$"),
) -> list[dict]:
    if USE_MICROSERVICES:
        url = f"{MCP_BASES['library']}/search"
        params = {}
        if query is not None:
            params["query"] = query
        if status is not None:
            params["status"] = status
        resp = _http_request_with_retries("GET", url, params=params)
        return resp.json()
    return library_server.search_books(query=query, status=status)


@app.get("/api/library/stats")
def library_stats() -> dict[str, int]:
    if USE_MICROSERVICES:
        url = f"{MCP_BASES['library']}/stats"
        resp = _http_request_with_retries("GET", url)
        return resp.json()
    return library_server.stats()


@app.post("/api/library/books/{book_id}/reserve")
def reserve_book(book_id: str) -> dict[str, Any]:
    if USE_MICROSERVICES:
        url = f"{MCP_BASES['library']}/books/{book_id}/reserve"
        try:
            resp = _http_request_with_retries("POST", url)
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                import json
                try: 
                    detail = e.response.json().get("detail", "Conflict")
                except: 
                    detail = e.response.text
                raise HTTPException(status_code=409, detail=detail)
            elif e.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Book not found.")
            raise HTTPException(status_code=500, detail=str(e))

    for book in LIBRARY_BOOKS:
        if book["id"] == book_id:
            if book["status"] != "available":
                raise HTTPException(status_code=409, detail="Only available books can be reserved.")
            book["status"] = "reserved"
            book["due"] = "2026-06-15"
            return {"message": "Book reserved successfully.", "book": book}
    raise HTTPException(status_code=404, detail="Book not found.")


@app.get("/api/cafeteria/menu/{meal}", response_model=MenuResponse)
def get_menu(meal: str) -> dict:
    if USE_MICROSERVICES:
        url = f"{MCP_BASES['cafeteria']}/menu/{meal}"
        resp = _http_request_with_retries("GET", url)
        return resp.json()
    return cafeteria_server.get_menu(meal)


@app.get("/api/cafeteria/menu")
def get_all_menus() -> dict:
    if USE_MICROSERVICES:
        url = f"{MCP_BASES['cafeteria']}/menus"
        resp = _http_request_with_retries("GET", url)
        data = resp.json()
        return {
            "menus": {k: v["items"] for k, v in data.items()},
            "timings": {k: v["timing"] for k, v in data.items()}
        }
    return {"menus": MENU, "timings": CAFETERIA_TIMINGS}


@app.get("/api/events", response_model=list[Event])
def list_events(tag: str | None = None, limit: int | None = Query(default=None, ge=1, le=20)) -> list[dict]:
    if USE_MICROSERVICES:
        url = f"{MCP_BASES['events']}/list"
        params = {}
        if tag is not None:
            params["tag"] = tag
        if limit is not None:
            params["limit"] = limit
        resp = _http_request_with_retries("GET", url, params=params)
        return resp.json()
    return events_server.list_events(tag=tag, limit=limit)


@app.get("/api/academics", response_model=dict)
def academics_summary() -> dict:
    if USE_MICROSERVICES:
        url = f"{MCP_BASES['academics']}/summary"
        resp = _http_request_with_retries("GET", url)
        return resp.json()
    return academics_server.summary()


@app.get("/api/academics/courses", response_model=list[Course])
def list_courses() -> list[dict]:
    return COURSES


@app.get("/api/academics/low-attendance", response_model=list[Course])
def low_attendance(threshold: int = Query(default=75, ge=0, le=100)) -> list[dict]:
    if USE_MICROSERVICES:
        url = f"{MCP_BASES['academics']}/low-attendance"
        resp = _http_request_with_retries("GET", url, params={"threshold": threshold})
        return resp.json()
    return academics_server.low_attendance(threshold=threshold)


@app.get("/api/notices", response_model=list[Notice])
def list_notices(urgent: bool | None = None, limit: int | None = Query(default=None, ge=1, le=20)) -> list[dict]:
    if USE_MICROSERVICES:
        url = f"{MCP_BASES['notices']}/list"
        params = {}
        if urgent is not None:
            params["urgent"] = urgent
        if limit is not None:
            params["limit"] = limit
        resp = _http_request_with_retries("GET", url, params=params)
        return resp.json()
    return notices_server.list_notices(urgent=urgent, limit=limit)


@app.post("/api/assistant/query", response_model=AssistantResponse)
def assistant_query(payload: AssistantRequest) -> dict[str, Any]:
    return run_assistant(payload.message, provider=payload.provider, api_key=payload.api_key)


@app.get("/api/mcp/library/search")
def mcp_library_search(query: str | None = None, status: str | None = Query(default=None, pattern="^(available|borrowed|reserved)$")) -> list[dict]:
    return SERVERS["library.search_books"](query=query, status=status)


@app.get("/api/mcp/cafeteria/menu")
def mcp_cafeteria_menu(meal: str = "lunch") -> dict:
    return SERVERS["cafeteria.get_menu"](meal=meal)


@app.get("/api/mcp/events")
def mcp_events(limit: int | None = Query(default=None, ge=1, le=50)) -> list[dict]:
    return SERVERS["events.list_events"](limit=limit)


@app.get("/api/mcp/academics/summary")
def mcp_academics_summary() -> dict:
    return SERVERS["academics.summary"]()


@app.get("/api/mcp/notices")
def mcp_notices(limit: int | None = Query(default=None, ge=1, le=50)) -> list[dict]:
    return SERVERS["notices.list_notices"](limit=limit)


@app.get("/api/mcp/tools")
def list_mcp_tools() -> dict[str, list[str]]:
    return {"tools": sorted(SERVERS.keys())}


@app.post("/api/mcp/call", response_model=McpToolResult)
def call_mcp_tool(payload: McpToolCall) -> dict[str, Any]:
    if payload.tool not in SERVERS:
        raise HTTPException(status_code=404, detail=f"Unknown MCP tool '{payload.tool}'.")
    try:
        result = SERVERS[payload.tool](**payload.arguments)
    except TypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"tool": payload.tool, "result": result}
