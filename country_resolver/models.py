from dataclasses import dataclass


@dataclass(frozen=True)
class CountryResolution:
    lat: float | None
    lon: float | None
    country_code: str
    country_source: str
    country_lookup_note: str
    distance_deg: float | None = None
    matched_country_name: str = ""