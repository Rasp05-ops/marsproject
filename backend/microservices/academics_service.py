from __future__ import annotations

from fastapi import FastAPI, Query

from app.mcp_servers.academics import academics_server

app = FastAPI(title="Academics MCP Service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "mcp_academics"}


@app.get("/summary")
def summary():
    return academics_server.summary()


@app.get("/low-attendance")
def low_attendance(threshold: int = Query(default=75, ge=0, le=100)):
    return academics_server.low_attendance(threshold=threshold)
