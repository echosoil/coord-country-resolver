import math
from pathlib import Path

import shapefile
from shapely.geometry import Point
from shapely.geometry import shape as shp_shape

try:
    import reverse_geocoder as rg
except Exception:  # pragma: no cover
    rg = None

from .models import CountryResolution
from .settings import ResolverSettings, load_settings


BAD_NUM = {"", " ", "-", "NA", "N/A", "NULL", "NONE", "NAN", "null", "None", "nan"}


def coord_to_float(value) -> float | None:
    if value is None:
        return None

    s = str(value).strip().replace(",", ".")
    if s in BAD_NUM:
        return None

    try:
        x = float(s)
    except Exception:
        return None

    if not math.isfinite(x):
        return None

    return x


def clean_iso2(value) -> str:
    s = str(value or "").strip().upper()
    if s in {"", "-99", "NULL", "NONE", "NAN"}:
        return ""
    if len(s) == 2 and s.isalpha():
        return s
    return ""


def record_get(record, field_names: list[str], name: str, default=""):
    if name not in field_names:
        return default

    try:
        return record[field_names.index(name)]
    except Exception:
        return default


def best_iso2_from_record(record, field_names: list[str]) -> str:
    """
    Natural Earth may have ISO_A2=-99 for some geometries.
    Try several fields before giving up.
    """
    for field in ("ISO_A2_EH", "ISO_A2", "WB_A2", "POSTAL"):
        iso2 = clean_iso2(record_get(record, field_names, field))
        if iso2:
            return iso2

    return ""


class CountryResolver:
    def __init__(self, settings: ResolverSettings | None = None):
        self.settings = settings or load_settings()
        self._country_shapes: list[dict] = []

    def load(self) -> None:
        shp_path = Path(self.settings.country_shp)

        if not shp_path.exists():
            raise FileNotFoundError(f"Country shapefile not found: {shp_path}")

        reader = shapefile.Reader(str(shp_path))
        field_names = [f[0] for f in reader.fields[1:]]

        shapes = []

        for sr in reader.shapeRecords():
            geom = shp_shape(sr.shape.__geo_interface__)
            record = sr.record

            iso2 = best_iso2_from_record(record, field_names)

            name = (
                record_get(record, field_names, "ADMIN")
                or record_get(record, field_names, "NAME")
                or record_get(record, field_names, "NAME_EN")
                or ""
            )

            shapes.append(
                {
                    "geom": geom,
                    "iso2": iso2,
                    "name": str(name or ""),
                }
            )

        self._country_shapes = shapes

    def resolve(self, lat, lon, *, debug: bool = False) -> CountryResolution:
        lat_f = coord_to_float(lat)
        lon_f = coord_to_float(lon)

        if lat_f is None or lon_f is None:
            return CountryResolution(
                lat=lat_f,
                lon=lon_f,
                country_code="",
                country_source="",
                country_lookup_note="invalid_or_missing_coordinates",
            )

        if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
            return CountryResolution(
                lat=lat_f,
                lon=lon_f,
                country_code="",
                country_source="",
                country_lookup_note="coordinates_out_of_range",
            )

        if not self._country_shapes:
            self.load()

        point = Point(lon_f, lat_f)

        exact = self._resolve_exact(point)
        if exact is not None:
            iso2, name = exact
            return CountryResolution(
                lat=lat_f,
                lon=lon_f,
                country_code=iso2,
                country_source="shapefile_exact",
                country_lookup_note="",
                matched_country_name=name,
            )

        nearest = self._resolve_nearest(point, lat_f, lon_f)
        if nearest is not None:
            iso2, name, distance_deg = nearest
            return CountryResolution(
                lat=lat_f,
                lon=lon_f,
                country_code=iso2,
                country_source="shapefile_nearest",
                country_lookup_note="nearest_polygon_within_tolerance",
                distance_deg=distance_deg,
                matched_country_name=name,
            )

        reverse = self._resolve_reverse_geocoder(lat_f, lon_f)
        if reverse:
            return CountryResolution(
                lat=lat_f,
                lon=lon_f,
                country_code=reverse,
                country_source="reverse_geocoder",
                country_lookup_note="shapefile_lookup_failed_reverse_geocoder_used",
            )

        return CountryResolution(
            lat=lat_f,
            lon=lon_f,
            country_code="",
            country_source="",
            country_lookup_note="country_lookup_failed",
        )

    def _resolve_exact(self, point: Point) -> tuple[str, str] | None:
        for item in self._country_shapes:
            iso2 = item["iso2"]
            if not iso2:
                continue

            try:
                if item["geom"].covers(point):
                    return iso2, item["name"]
            except Exception:
                continue

        return None

    def _resolve_nearest(
        self,
        point: Point,
        lat: float,
        lon: float,
    ) -> tuple[str, str, float] | None:
        tolerance = self.settings.country_lookup_tolerance_deg
        blacklist = self.settings.country_nearest_blacklist

        candidates = []

        for item in self._country_shapes:
            iso2 = str(item["iso2"] or "").strip().upper()
            if not iso2:
                continue

            if iso2 in blacklist:
                continue

            geom = item["geom"]

            try:
                minx, miny, maxx, maxy = geom.bounds

                if lon < minx - tolerance:
                    continue
                if lon > maxx + tolerance:
                    continue
                if lat < miny - tolerance:
                    continue
                if lat > maxy + tolerance:
                    continue

                distance_deg = geom.distance(point)
                if distance_deg <= tolerance:
                    candidates.append((distance_deg, iso2, item["name"]))
            except Exception:
                continue

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        distance_deg, iso2, name = candidates[0]

        return iso2, name, distance_deg

    def _resolve_reverse_geocoder(self, lat: float, lon: float) -> str:
        if rg is None:
            return ""

        try:
            result = rg.search([(lat, lon)], mode=1)
            if result:
                return str(result[0].get("cc") or "").strip().upper()
        except Exception:
            return ""

        return ""