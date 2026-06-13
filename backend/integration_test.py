#!/usr/bin/env python3
"""Simple integration smoke tests for the CampusIQ stack.

Run this after services are up (or while docker compose is running).
"""
import sys
import time
import httpx

BASE = "http://localhost:8000"


def expect_ok(path: str):
    url = BASE + path
    r = httpx.get(url, timeout=10.0)
    print(path, r.status_code)
    r.raise_for_status()
    return r.json()


def test_assistant():
    url = BASE + "/api/assistant/query"
    payload = {"message": "What's for lunch today?"}
    r = httpx.post(url, json=payload, timeout=20.0)
    print("assistant:", r.status_code)
    r.raise_for_status()
    data = r.json()
    assert "answer" in data
    print("assistant answer:", data.get("answer")[:200])


def main():
    # health endpoints
    try:
        expect_ok("/health")
        expect_ok("/api/dashboard")
        expect_ok("/api/library/books")
        expect_ok("/api/cafeteria/menu")
        expect_ok("/api/events")
        expect_ok("/api/academics")
        expect_ok("/api/notices")
    except Exception as exc:
        print("Smoke failed during basic endpoints:", exc)
        sys.exit(2)

    try:
        test_assistant()
    except Exception as exc:
        print("Assistant test failed:", exc)
        sys.exit(3)

    print("All smoke tests passed.")


if __name__ == "__main__":
    main()
