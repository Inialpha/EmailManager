"""Strict runtime schema for Executive AI email insight responses."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EventInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    description: str


class ActionInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    due_date: Optional[str] = None


class DeadlineInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    date: Optional[str] = None
    description: str


class ReminderInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    datetime: Optional[str] = None
    reason: str


class EmailInsight(BaseModel):
    """Exact response contract consumed by Executive AI."""

    model_config = ConfigDict(extra="forbid")

    id: str
    thread_id: Optional[str] = None
    sender: Optional[str] = None
    subject: str
    is_important: bool
    summary: str
    events: List[EventInsight] = Field(default_factory=list)
    actions: List[ActionInsight] = Field(default_factory=list)
    deadlines: List[DeadlineInsight] = Field(default_factory=list)
    reminders: List[ReminderInsight] = Field(default_factory=list)


__all__ = [
    "ActionInsight",
    "DeadlineInsight",
    "EmailInsight",
    "EventInsight",
    "ReminderInsight",
]
