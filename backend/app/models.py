from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Book(BaseModel):
    id: str
    title: str
    author: str
    status: Literal["available", "borrowed", "reserved"]
    due: str | None = None


class MenuResponse(BaseModel):
    meal: str
    items: list[str]
    timing: str


class Event(BaseModel):
    id: str
    name: str
    org: str
    date: str
    time: str
    venue: str
    tag: str


class Notice(BaseModel):
    id: str
    title: str
    from_: str = Field(alias="from")
    date: str
    urgent: bool


class Course(BaseModel):
    code: str
    name: str
    prof: str
    attendance: int
    grade: str


class Exam(BaseModel):
    course_code: str
    course: str
    date: str
    time: str


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    student_id: str | None = None
    provider: str | None = None
    api_key: str | None = None


class AssistantResponse(BaseModel):
    answer: str
    routed_tools: list[str]
    results: dict[str, Any]


class McpToolCall(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class McpToolResult(BaseModel):
    tool: str
    result: Any
