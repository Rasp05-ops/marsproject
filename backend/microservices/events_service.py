from __future__ import annotations

from fastapi import FastAPI, Query

from app.mcp_servers.events import events_server

app = FastAPI(title="Events MCP Service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "mcp_events"}


@app.get("/list")
def list_events(tag: str | None = None, limit: int | None = Query(default=None, ge=1, le=50)):
    return events_server.list_events(tag=tag, limit=limit)
