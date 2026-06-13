from __future__ import annotations

from fastapi import FastAPI, Query

from app.mcp_servers.cafeteria import cafeteria_server

app = FastAPI(title="Cafeteria MCP Service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "mcp_cafeteria"}


@app.get("/menu/{meal}")
def get_menu(meal: str = "lunch"):
    return cafeteria_server.get_menu(meal)


@app.get("/menus")
def all_menus():
    return cafeteria_server.all_menus()
