from __future__ import annotations

from typing import Any


from app.mcp_servers import SERVERS
from app.services import llm


def _contains_any(message: str, terms: list[str]) -> bool:
    return any(term in message for term in terms)


def route_tools(message: str) -> list[tuple[str, dict[str, Any]]]:
    text = message.lower()
    routes: list[tuple[str, dict[str, Any]]] = []

    if _contains_any(text, ["book", "library", "borrow", "reserve", "available"]):
        routes.append(("library.search_books", {}))
        routes.append(("library.stats", {}))

    if _contains_any(text, ["food", "menu", "eat", "cafeteria", "breakfast", "lunch", "snacks", "dinner"]):
        meal = "lunch"
        for candidate in ["breakfast", "lunch", "snacks", "dinner"]:
            if candidate in text:
                meal = candidate
                break
        routes.append(("cafeteria.get_menu", {"meal": meal}))

    if _contains_any(text, ["event", "workshop", "fest", "club", "competition", "summit"]):
        routes.append(("events.list_events", {"limit": 5}))

    if _contains_any(text, ["attendance", "cgpa", "grade", "course", "exam", "schedule", "timetable", "end sem"]):
        routes.append(("academics.summary", {}))
        if "attendance" in text:
            routes.append(("academics.low_attendance", {"threshold": 75}))

    if _contains_any(text, ["notice", "circular", "fee", "payment", "deadline", "scholarship", "hostel"]):
        routes.append(("notices.list_notices", {"limit": 5}))

    if not routes:
        routes = [
            ("library.stats", {}),
            ("cafeteria.get_menu", {"meal": "lunch"}),
            ("events.list_events", {"limit": 3}),
            ("notices.list_notices", {"urgent": True}),
        ]

    return routes


def call_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
    if tool_name not in SERVERS:
        raise KeyError(f"Unknown tool: {tool_name}")
    return SERVERS[tool_name](**(arguments or {}))


def answer_from_results(message: str, results: dict[str, Any]) -> str:
    text = message.lower()
    parts: list[str] = []

    if "library.search_books" in results:
        stats = results.get("library.stats", {})
        available = stats.get("available", 0)
        books = results["library.search_books"][:3]
        names = ", ".join(book["title"] for book in books) or "no matching books"
        parts.append(f"Library: {available} books are available right now. Top matches: {names}.")

    if "cafeteria.get_menu" in results:
        menu = results["cafeteria.get_menu"]
        items = ", ".join(menu["items"])
        parts.append(f"Cafeteria: {menu['meal'].title()} is served from {menu['timing']}. Items: {items}.")

    if "events.list_events" in results:
        events = results["events.list_events"]
        if events:
            first = events[0]
            parts.append(f"Events: next up is {first['name']} on {first['date']} at {first['time']} in {first['venue']}.")
        else:
            parts.append("Events: I could not find upcoming campus events right now.")

    if "academics.low_attendance" in results and results["academics.low_attendance"]:
        courses = ", ".join(course["name"] for course in results["academics.low_attendance"])
        parts.append(f"Attendance: your low-attendance course is {courses}. Try to attend the next few classes to get back above 75%.")

    if "academics.summary" in results:
        summary = results["academics.summary"]
        if "exam" in text or "schedule" in text or "timetable" in text:
            exams = ", ".join(f"{exam['course_code']} on {exam['date']}" for exam in summary["exams"])
            parts.append(f"Exams: {exams}.")
        elif "academics.low_attendance" not in results:
            parts.append(f"Academics: your CGPA is {summary['cgpa']} and average attendance is {summary['average_attendance']}%.")

    if "notices.list_notices" in results:
        notices = results["notices.list_notices"]
        titles = ", ".join(notice["title"] for notice in notices[:3])
        parts.append(f"Notices: {titles}.")

    if parts:
        return " ".join(parts)

    return "I checked the campus sources. Ask me about library books, cafeteria menus, events, academics, or notices."


def run_assistant(message: str, provider: str | None = None, api_key: str | None = None) -> dict[str, Any]:
    # Try to get a plan from the LLM first. If LLM is not configured or planning
    # fails, fall back to the existing rule-based router.
    routed = llm.plan_tools(message, provider=provider, api_key=api_key) or route_tools(message)
    results = {tool_name: call_tool(tool_name, args) for tool_name, args in routed}

    # Let the LLM synthesize the final answer from results when available.
    answer = llm.generate_answer(message, results, provider=provider, api_key=api_key) or answer_from_results(message, results)

    return {
        "answer": answer,
        "routed_tools": [tool_name for tool_name, _ in routed],
        "results": results,
    }
