from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, Iterable, Optional, Tuple


DATE_KEY_HINTS = (
    "date",
    "time",
    "open",
    "close",
    "start",
    "end",
    "deadline",
    "created",
    "modified",
    "updated",
    "expires",
)

DATETIME_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
)


def _to_int(value: Optional[str]) -> Optional[int]:
    if value in (None, "", "None"):
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _to_float(value: Optional[str]) -> Optional[float]:
    if value in (None, "", "None"):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _to_bool(value: Optional[str]) -> Optional[bool]:
    if value in (None, "", "None"):
        return None
    lower = str(value).strip().lower()
    if lower in {"1", "true", "yes"}:
        return True
    if lower in {"0", "false", "no"}:
        return False
    return None


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    sanitized = value.strip()
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(sanitized, fmt)
        except ValueError:
            continue
    return None


def _snake_case(name: str) -> str:
    if "_" in name:
        return name.lower()
    first_pass = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", first_pass).lower()


def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for key, value in payload.items():
        normalized[_snake_case(key)] = value
    return normalized


@dataclass
class SonaStudy:
    experiment_id: int
    name: str
    is_active: Optional[bool]
    is_approved: Optional[bool]
    web_flag: Optional[int]
    survey_flag: Optional[int]
    duration_minutes: Optional[int]
    credit_value: Optional[float]
    researcher_id: Optional[int]
    department: Optional[str]
    location: Optional[str]
    url: Optional[str]
    code: Optional[str]
    description: Optional[str]
    raw: Dict[str, Any] = field(default_factory=dict)
    timeline: Dict[str, datetime] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "SonaStudy":
        normalized = normalize_payload(payload)
        experiment_id = _to_int(normalized.get("experiment_id"))
        if experiment_id is None:
            raise ValueError("SONA study payload missing experiment_id.")

        name = (
            normalized.get("study_name")
            or normalized.get("name")
            or normalized.get("experiment_name")
            or f"Study {experiment_id}"
        )

        timeline = cls._build_timeline(normalized)
        return cls(
            experiment_id=experiment_id,
            name=name,
            is_active=_to_bool(
                normalized.get("is_active") or normalized.get("active")
            ),
            is_approved=_to_bool(
                normalized.get("is_approved") or normalized.get("approved")
            ),
            web_flag=_to_int(normalized.get("web_flag")),
            survey_flag=_to_int(normalized.get("survey_flag")),
            duration_minutes=_to_int(
                normalized.get("duration_minutes")
                or normalized.get("duration")
            ),
            credit_value=_to_float(
                normalized.get("credit_value") or normalized.get("credits")
            ),
            researcher_id=_to_int(
                normalized.get("researcher_id")
                or normalized.get("primary_researcher_id")
            ),
            department=normalized.get("department_name")
            or normalized.get("department"),
            location=normalized.get("location"),
            url=normalized.get("study_url") or normalized.get("url"),
            code=normalized.get("study_code")
            or normalized.get("experiment_code"),
            description=normalized.get("study_description")
            or normalized.get("description"),
            raw=normalized,
            timeline=timeline,
        )

    @staticmethod
    def _build_timeline(payload: Dict[str, Any]) -> Dict[str, datetime]:
        timeline: Dict[str, datetime] = {}
        for key, value in payload.items():
            if not isinstance(value, str):
                continue
            lowered = key.lower()
            if not any(hint in lowered for hint in DATE_KEY_HINTS):
                continue
            parsed = _parse_datetime(value)
            if parsed:
                timeline[key] = parsed
        return timeline

    @property
    def is_lab_study(self) -> bool:
        return (self.web_flag or 0) == 0

    @property
    def is_online(self) -> bool:
        flag = self.web_flag or 0
        return flag == 1 or (self.survey_flag or 0) == 1

    @property
    def primary_date(self) -> Optional[datetime]:
        if not self.timeline:
            return None
        return min(self.timeline.values())

    def date_window(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        if not self.timeline:
            return (None, None)
        ordered = sorted(self.timeline.values())
        return (ordered[0], ordered[-1])

    def matches_window(
        self,
        start: Optional[datetime],
        end: Optional[datetime],
    ) -> bool:
        if start is None and end is None:
            return True
        study_start, study_end = self.date_window()
        if study_start is None and study_end is None:
            return False

        reference_start = study_start or study_end
        reference_end = study_end or study_start

        if start and reference_end and reference_end < start:
            return False
        if end and reference_start and reference_start > end:
            return False
        return True

    def to_dict(self, include_raw: bool = False) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "experimentId": self.experiment_id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "durationMinutes": self.duration_minutes,
            "creditValue": self.credit_value,
            "isActive": self.is_active,
            "isApproved": self.is_approved,
            "webFlag": self.web_flag,
            "surveyFlag": self.survey_flag,
            "isLabStudy": self.is_lab_study,
            "isOnlineStudy": self.is_online,
            "researcherId": self.researcher_id,
            "department": self.department,
            "location": self.location,
            "url": self.url,
            "timeline": {
                key: value.isoformat()
                for key, value in self.timeline.items()
            },
        }
        if include_raw:
            base["raw"] = self.raw
        return base


def filter_by_date_range(
    studies: Iterable[SonaStudy],
    start: Optional[datetime],
    end: Optional[datetime],
) -> Iterable[SonaStudy]:
    for study in studies:
        if study.matches_window(start, end):
            yield study
