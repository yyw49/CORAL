from __future__ import annotations

from datetime import date, datetime, time
from functools import lru_cache
from typing import List, Optional

from .dto import SonaStudySchedule, filter_by_date_range
from .sona_client import SonaApiClient


@lru_cache(maxsize=1)
def _client() -> SonaApiClient:
    return SonaApiClient()


def _as_datetime(value: Optional[date], *, end_of_day: bool = False) -> Optional[datetime]:
    if value is None:
        return None
    return datetime.combine(
        value,
        time.max if end_of_day else time.min,
    )


def fetch_all_active_lab_studies() -> List[SonaStudySchedule]:
    """
    Fetch the default set of SONA study schedules using the configured window.
    """
    return _client().get_study_schedule()


def fetch_studies_for_window(
    *,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[SonaStudySchedule]:
    """
    Fetch SONA study schedules and optionally filter them down to the requested window.
    """
    studies = _client().get_study_schedule(
        start_date=start_date,
        end_date=end_date,
    )
    start_dt = _as_datetime(start_date) if start_date else None
    end_dt = _as_datetime(end_date, end_of_day=True) if end_date else None

    if start_dt or end_dt:
        studies = list(filter_by_date_range(studies, start_dt, end_dt))
    return studies
