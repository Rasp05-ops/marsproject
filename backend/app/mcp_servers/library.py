from __future__ import annotations

from app.data import LIBRARY_BOOKS


class LibraryServer:
    source = "central_library"

    def search_books(self, query: str | None = None, status: str | None = None) -> list[dict]:
        books = LIBRARY_BOOKS
        if query:
            q = query.lower()
            books = [book for book in books if q in book["title"].lower() or q in book["author"].lower()]
        if status:
            books = [book for book in books if book["status"] == status]
        return books

    def stats(self) -> dict:
        return {
            "available": len([book for book in LIBRARY_BOOKS if book["status"] == "available"]),
            "borrowed": len([book for book in LIBRARY_BOOKS if book["status"] == "borrowed"]),
            "reserved": len([book for book in LIBRARY_BOOKS if book["status"] == "reserved"]),
        }


library_server = LibraryServer()
