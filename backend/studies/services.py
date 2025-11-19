from __future__ import annotations

from datetime import date, datetime, time
from functools import lru_cache
from typing import Iterable, List, Optional

from .dto import SonaStudy, filter_by_date_range
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


def fetch_all_active_lab_studies() -> List[SonaStudy]:
    """
    Fetch the default set of SONA studies (active, approved, non-online).
    """
    studies = _client().get_study_list()
    return [study for study in studies if study.is_lab_study]


def fetch_studies_for_window(
    *,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[SonaStudy]:
    """
    Fetch SONA studies and optionally filter them down to the requested window.
    """
    studies = fetch_all_active_lab_studies()
    start_dt = _as_datetime(start_date) if start_date else None
    end_dt = _as_datetime(end_date, end_of_day=True) if end_date else None

    if start_dt or end_dt:
        studies = list(filter_by_date_range(studies, start_dt, end_dt))
    return studies
