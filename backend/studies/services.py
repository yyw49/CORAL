from __future__ import annotations

from datetime import date, datetime, time
from functools import lru_cache
from typing import List, Optional

from django.conf import settings

from .dto import SonaStudySchedule, filter_by_date_range
from .sona_client import SonaApiClient


@lru_cache(maxsize=2)
def _client(site: str = "mor") -> Optional[SonaApiClient]:
    if site == "mor":
        return SonaApiClient()
    if site == "mkt":
        mkt_conf = getattr(settings, "SONA_MKT", {})
        base = mkt_conf.get("BASE_URL") or ""
        key = mkt_conf.get("KEY") or ""
        if not base or not key:
            return None
        from .sona_client import SonaApiConfig

        return SonaApiClient(
            config=SonaApiConfig.from_values(
                base_url=base,
                api_key=key,
            )
        )
    return None


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
    schedules: List[SonaStudySchedule] = []
    for site_label in ("mor", "mkt"):
        client = _client(site_label)
        if not client:
            continue
        site_schedules = client.get_study_schedule()
        for s in site_schedules:
            s.site = site_label
        schedules.extend(site_schedules)
    return schedules


def fetch_studies_for_window(
    *,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[SonaStudySchedule]:
    """
    Fetch SONA study schedules and optionally filter them down to the requested window.
    """
    studies: List[SonaStudySchedule] = []
    for site_label in ("mor", "mkt"):
        client = _client(site_label)
        if not client:
            continue
        site_studies = client.get_study_schedule(
            start_date=start_date,
            end_date=end_date,
        )
        for s in site_studies:
            s.site = site_label
        studies.extend(site_studies)
    start_dt = _as_datetime(start_date) if start_date else None
    end_dt = _as_datetime(end_date, end_of_day=True) if end_date else None

    if start_dt or end_dt:
        studies = list(filter_by_date_range(studies, start_dt, end_dt))
    return studies
