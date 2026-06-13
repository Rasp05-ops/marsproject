from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from app.mcp_servers.library import library_server

app = FastAPI(title="Library MCP Service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "mcp_library"}


@app.get("/search")
def search_books(query: str | None = None, status: str | None = Query(default=None, pattern="^(available|borrowed|reserved)$")):
    return library_server.search_books(query=query, status=status)


@app.get("/stats")
def stats():
    return library_server.stats()


@app.post("/books/{book_id}/reserve")
def reserve(book_id: str):
    for book in library_server._books if hasattr(library_server, "_books") else []:
        if book["id"] == book_id:
            if book["status"] != "available":
                raise HTTPException(status_code=409, detail="Only available books can be reserved.")
            book["status"] = "reserved"
            book["due"] = "2026-06-15"
            return {"message": "Book reserved successfully.", "book": book}
    # fallback to library server method
    try:
        return library_server.reserve(book_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Book not found.")
