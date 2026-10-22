"""ISO-week and festival-calendar helpers."""
from __future__ import annotations

import re
from datetime import date, timedelta

import pandas as pd

WEEK_PATTERN = re.compile(r"^(\d{4})-W(\d{2})$")


def parse_iso_week(label: str) -> tuple[int, int] | None:
    """'2026-W27' -> (2026, 27); None if malformed or not a real ISO week."""
    m = WEEK_PATTERN.match(str(label).strip())
    if not m:
        return None
    year, week = int(m.group(1)), int(m.group(2))
    try:
        date.fromisocalendar(year, week, 1)
    except ValueError:
        return None
    return year, week


def week_start(year: int, week: int) -> date:
    return date.fromisocalendar(year, week, 1)


def week_end(year: int, week: int) -> date:
    return date.fromisocalendar(year, week, 7)


def week_month(year: int, week: int) -> str:
    """Month a week belongs to, by the ISO convention (the week's Thursday).

    ASSUMPTION: the case defines festival *months*, the sales file has *weeks*.
    A week that straddles two months is assigned to the month of its Thursday.
    """
    thursday = date.fromisocalendar(year, week, 4)
    return f"{thursday.year:04d}-{thursday.month:02d}"


def week_label(year: int, week: int) -> str:
    return f"{year:04d}-W{week:02d}"


def shift_week(year: int, week: int, n: int) -> tuple[int, int]:
    d = week_start(year, week) + timedelta(weeks=n)
    iso = d.isocalendar()
    return iso[0], iso[1]


def festival_lookup(calendar: pd.DataFrame) -> dict[str, bool]:
    """Year_Month -> is_festival from the validated calendar frame."""
    return dict(zip(calendar["Year_Month"], calendar["is_festival"]))


def is_festival_month(year_month: str, lookup: dict[str, bool]) -> bool | None:
    """None when the month is absent from calendar.csv (cannot be determined)."""
    return lookup.get(year_month)
