from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Union
from xml.etree import ElementTree as ET

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import requests

from .dto import SonaStudySchedule


class SonaAPIError(RuntimeError):
    """Raised when the SONA API returns an error response."""


def _strip_tag(value: str) -> str:
    if "}" in value:
        return value.split("}", 1)[1]
    return value


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


@dataclass
class SonaApiConfig:
    base_url: str
    api_key: str
    timeout: int
    location_id: int
    lab_only: int
    schedule_start: str
    schedule_end: str

    @classmethod
    def from_settings(cls) -> "SonaApiConfig":
        config = getattr(settings, "SONA_API", None)
        if not config:
            raise ImproperlyConfigured("SONA_API settings not defined.")
        base_url = (config.get("BASE_URL") or "").rstrip("/")
        api_key = config.get("KEY") or ""
        if not base_url or not api_key:
            raise ImproperlyConfigured(
                "SONA_API BASE_URL and KEY are required."
            )
        return cls(
            base_url=base_url,
            api_key=api_key,
            timeout=int(config.get("TIMEOUT", 15)),
            location_id=int(config.get("LOCATION_ID", -2)),
            lab_only=int(config.get("LAB_ONLY", 1)),
            schedule_start=str(config.get("SCHEDULE_START", "1900-01-01")),
            schedule_end=str(config.get("SCHEDULE_END", "2100-01-01")),
        )

    @classmethod
    def from_values(
        cls,
        *,
        base_url: str,
        api_key: str,
        timeout: Optional[int] = None,
        location_id: Optional[int] = None,
        lab_only: Optional[int] = None,
        schedule_start: Optional[str] = None,
        schedule_end: Optional[str] = None,
    ) -> "SonaApiConfig":
        defaults = cls.from_settings()
        url = (base_url or "").rstrip("/")
        key = api_key or ""
        if not url or not key:
            raise ImproperlyConfigured("SONA API base_url and api_key are required.")
        return cls(
            base_url=url,
            api_key=key,
            timeout=timeout or defaults.timeout,
            location_id=location_id if location_id is not None else defaults.location_id,
            lab_only=lab_only if lab_only is not None else defaults.lab_only,
            schedule_start=schedule_start or defaults.schedule_start,
            schedule_end=schedule_end or defaults.schedule_end,
        )


class SonaApiClient:
    """
    Thin wrapper around the SONA API that exposes what we need for
    SonaGetStudyScheduleList.
    """

    def __init__(
        self,
        config: Optional[SonaApiConfig] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.config = config or SonaApiConfig.from_settings()
        self.session = session or requests.Session()

    def get_study_schedule(
        self,
        *,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        location_id: Optional[int] = None,
        lab_only: Optional[int] = None,
    ) -> List[SonaStudySchedule]:
        params = {
            "api_key": self.config.api_key,
            "location_id": location_id
            if location_id is not None
            else self.config.location_id,
            "start_date": self._format_date(start_date)
            or self.config.schedule_start,
            "end_date": self._format_date(end_date)
            or self.config.schedule_end,
            "lab_only": lab_only
            if lab_only is not None
            else self.config.lab_only,
        }
        response_text = self._request("SonaGetStudyScheduleList", params)
        return self._parse_studies(response_text)

    @staticmethod
    def _format_date(value: Optional[Union[str, date]]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.isoformat()

    def _request(
        self, resource: str, params: Dict[str, Union[str, int]]
    ) -> str:
        url = f"{self.config.base_url}/{resource}"
        try:
            response = self.session.get(
                url, params=params, timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            raise SonaAPIError(
                f"Unable to reach SONA API: {exc}"
            ) from exc

    def _parse_studies(self, payload: str) -> List[SonaStudySchedule]:
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            raise SonaAPIError(f"Invalid XML payload: {exc}") from exc

        errors = self._extract_errors(root)
        if errors:
            raise SonaAPIError("; ".join(errors))

        studies: List[SonaStudySchedule] = []
        for node in root.iter():
            if _strip_tag(node.tag) != "APIStudySchedule":
                continue
            study_payload = {
                _strip_tag(child.tag): _clean_text(child.text)
                for child in node
            }
            try:
                studies.append(SonaStudySchedule.from_payload(study_payload))
            except ValueError:
                # Skip malformed entries but keep the rest of the payload so
                # partial data does not prevent the user from seeing anything.
                continue
        return studies

    def _extract_errors(self, root: ET.Element) -> List[str]:
        errors: List[str] = []
        xsi_nil = "{http://www.w3.org/2001/XMLSchema-instance}nil"
        for node in root.iter():
            if _strip_tag(node.tag) != "Errors":
                continue
            if node.attrib.get(xsi_nil) == "true":
                continue
            text = " ".join(chunk.strip() for chunk in node.itertext())
            if text:
                errors.append(text)
        return errors
