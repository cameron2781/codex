from __future__ import annotations

from datetime import date, timedelta


def status_for_due_date(today: date, due: date) -> str:
    if today > due:
        return "overdue"
    if today + timedelta(days=7) >= due:
        return "due_soon"
    return "scheduled"
