from __future__ import annotations

from fastapi import FastAPI, Query

from app.mcp_servers.notices import notices_server

app = FastAPI(title="Notices MCP Service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "mcp_notices"}


@app.get("/list")
def list_notices(urgent: bool | None = None, limit: int | None = Query(default=None, ge=1, le=50)):
    return notices_server.list_notices(urgent=urgent, limit=limit)
