from __future__ import annotations

from app.data import NOTICES


class NoticesServer:
    source = "campus_notice_board"

    def list_notices(self, urgent: bool | None = None, limit: int | None = None) -> list[dict]:
        notices = NOTICES
        if urgent is not None:
            notices = [notice for notice in notices if notice["urgent"] is urgent]
        notices = sorted(notices, key=lambda notice: notice["date"], reverse=True)
        return notices[:limit] if limit else notices


notices_server = NoticesServer()
