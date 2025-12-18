from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional


DATE_FMT = "%Y-%m-%d"


def parse_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(value, DATE_FMT).date()


def format_date(value: date) -> str:
    return value.strftime(DATE_FMT)


def days_between(start: date, end: date) -> int:
    if end <= start:
        return 0
    return (end - start).days


def next_due_date(anchor: date, due_day: int) -> date:
    if due_day < 1 or due_day > 28:
        raise ValueError("due_day must be 1-28 to avoid month-end ambiguity")
    year = anchor.year
    month = anchor.month
    candidate = date(year, month, due_day)
    if candidate <= anchor:
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        candidate = date(year, month, due_day)
    return candidate


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
