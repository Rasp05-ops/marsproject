from __future__ import annotations

from app.data import EVENTS


class EventsServer:
    source = "student_activity_calendar"

    def list_events(self, tag: str | None = None, limit: int | None = None) -> list[dict]:
        events = EVENTS
        if tag:
            events = [event for event in events if event["tag"].lower() == tag.lower()]
        events = sorted(events, key=lambda event: event["date"])
        return events[:limit] if limit else events


events_server = EventsServer()
