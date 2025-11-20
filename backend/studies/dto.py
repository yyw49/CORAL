from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, Iterable, Optional


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
    "timeslot",
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
class SonaStudySchedule:
    experiment_id: int
    study_name: str
    timeslot_id: Optional[int]
    timeslot_date: Optional[datetime]
    duration_minutes: Optional[int]
    location: Optional[str]
    num_signed_up: Optional[int]
    num_students: Optional[int]
    researcher_id: Optional[int]
    survey_flag: Optional[int]
    web_flag: Optional[int]
    videoconf_flag: Optional[int]
    videoconf_url: Optional[str]
    raw: Dict[str, Any] = field(default_factory=dict)
    timeline: Dict[str, datetime] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "SonaStudySchedule":
        normalized = normalize_payload(payload)
        experiment_id = _to_int(normalized.get("experiment_id"))
        if experiment_id is None:
            raise ValueError("SONA schedule payload missing experiment_id.")

        timeslot_date = normalized.get("timeslot_date")
        parsed_timeslot = _parse_datetime(timeslot_date)
        timeline = cls._build_timeline(normalized)
        if parsed_timeslot:
            timeline.setdefault("timeslot_date", parsed_timeslot)

        return cls(
            experiment_id=experiment_id,
            study_name=normalized.get("study_name") or f"Study {experiment_id}",
            timeslot_id=_to_int(normalized.get("timeslot_id")),
            timeslot_date=parsed_timeslot,
            duration_minutes=_to_int(
                normalized.get("duration_minutes") or normalized.get("duration")
            ),
            location=normalized.get("location"),
            num_signed_up=_to_int(normalized.get("num_signed_up")),
            num_students=_to_int(normalized.get("num_students")),
            researcher_id=_to_int(normalized.get("researcher_id")),
            survey_flag=_to_int(normalized.get("survey_flag")),
            web_flag=_to_int(normalized.get("web_flag")),
            videoconf_flag=_to_int(normalized.get("videoconf_flag")),
            videoconf_url=normalized.get("videoconf_url"),
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

    def matches_window(
        self,
        start: Optional[datetime],
        end: Optional[datetime],
    ) -> bool:
        if start is None and end is None:
            return True
        target = self.timeslot_date or self._primary_timeline_point()
        if target is None:
            return False
        if start and target < start:
            return False
        if end and target > end:
            return False
        return True

    def _primary_timeline_point(self) -> Optional[datetime]:
        if not self.timeline:
            return None
        return sorted(self.timeline.values())[0]

    def to_dict(self, include_raw: bool = False) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "experimentId": self.experiment_id,
            "studyName": self.study_name,
            "timeslotId": self.timeslot_id,
            "timeslotDate": self.timeslot_date.isoformat()
            if self.timeslot_date
            else None,
            "durationMinutes": self.duration_minutes,
            "location": self.location,
            "numSignedUp": self.num_signed_up,
            "numStudents": self.num_students,
            "researcherId": self.researcher_id,
            "surveyFlag": self.survey_flag,
            "webFlag": self.web_flag,
            "videoconfFlag": self.videoconf_flag,
            "videoconfUrl": self.videoconf_url,
            "timeline": {
                key: value.isoformat()
                for key, value in self.timeline.items()
            },
        }
        if include_raw:
            base["raw"] = self.raw
        return base


def filter_by_date_range(
    studies: Iterable[SonaStudySchedule],
    start: Optional[datetime],
    end: Optional[datetime],
) -> Iterable[SonaStudySchedule]:
    for study in studies:
        if study.matches_window(start, end):
            yield study


# Alias for compatibility — any import expecting `Study` will get the SONA schedule.
Study = SonaStudySchedule
