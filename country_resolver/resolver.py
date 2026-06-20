import math
from pathlib import Path

import pycountry
import shapefile
from shapely.geometry import Point
from shapely.geometry import shape as shp_shape

try:
    import reverse_geocoder as rg
except Exception:  # pragma: no cover
    rg = None

try:
    import geopandas as gpd
except Exception:  # pragma: no cover
    gpd = None

from .models import CountryResolution
from .settings import ResolverSettings, load_settings


BAD_NUM = {"", " ", "-", "NA", "N/A", "NULL", "NONE", "NAN", "null", "None", "nan"}


def iso_to_iso2(value) -> str:
    s = str(value or "").strip().upper()

    if not s or s in {"-99", "NULL", "NONE", "NAN"}:
        return ""

    if len(s) == 2 and s.isalpha():
        return s

    if len(s) == 3 and s.isalpha():
        try:
            country = pycountry.countries.get(alpha_3=s)
            if country:
                return country.alpha_2
        except Exception:
            return ""

    return ""


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
    return iso_to_iso2(value)


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
        all_shapes = []

        for path in self.settings.country_boundary_files:
            path = Path(path)

            if not path.exists():
                raise FileNotFoundError(f"Boundary file not found: {path}")

            suffix = path.suffix.lower()

            if suffix == ".gpkg":
                all_shapes.extend(self._load_gpkg(path))
            elif suffix == ".shp":
                all_shapes.extend(self._load_shp(path))
            else:
                raise ValueError(f"Unsupported boundary file format: {path}")

        self._country_shapes = all_shapes

    def _load_shp(self, shp_path: Path) -> list[dict]:
        reader = shapefile.Reader(str(shp_path))
        field_names = [f[0] for f in reader.fields[1:]]

        dataset = "naturalearth" if "ne_" in str(shp_path).lower() else shp_path.stem

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

            if not iso2:
                continue

            shapes.append(
                {
                    "geom": geom,
                    "iso2": iso2,
                    "name": str(name or ""),
                    "dataset": dataset,
                }
            )

        return shapes

    def _load_gpkg(self, path: Path) -> list[dict]:
        if gpd is None:
            raise RuntimeError("geopandas is required to load GeoPackage boundary files")

        df = gpd.read_file(path, engine="pyogrio")

        if df.crs is not None and df.crs.to_epsg() != 4326:
            df = df.to_crs("EPSG:4326")

        dataset = (
            "geoboundaries"
            if "geobound" in str(path).lower()
            else path.stem
        )

        shapes = []

        for _, row in df.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue

            # geoBoundaries commonly uses shapeGroup for ISO3 and shapeName for country name.
            iso2 = ""
            for col in ("shapeISO", "shapeGroup", "ISO_A2", "iso_a2", "ADM0_A2"):
                if col in df.columns:
                    iso2 = iso_to_iso2(row.get(col))
                    if iso2:
                        break

            name = ""
            for col in ("shapeName", "shapeGroup", "ADMIN", "NAME", "name"):
                if col in df.columns:
                    value = row.get(col)
                    if value:
                        name = str(value)
                        break

            if not iso2:
                continue

            shapes.append(
                {
                    "geom": geom,
                    "iso2": iso2,
                    "name": name,
                    "dataset": dataset,
                }
            )

        return shapes

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
            iso2, name, dataset = exact
            return CountryResolution(
                lat=lat_f,
                lon=lon_f,
                country_code=iso2,
                country_source=f"{dataset}_exact",
                country_lookup_note="",
                distance_deg=0.0,
                matched_country_name=name,
            )

        nearest = self._resolve_nearest(point, lat_f, lon_f)
        if nearest is not None:
            iso2, name, distance_deg, dataset = nearest
            return CountryResolution(
                lat=lat_f,
                lon=lon_f,
                country_code=iso2,
                country_source=f"{dataset}_nearest",
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
                country_lookup_note="boundary_lookup_failed_reverse_geocoder_used",
            )

        return CountryResolution(
            lat=lat_f,
            lon=lon_f,
            country_code="",
            country_source="",
            country_lookup_note="country_lookup_failed",
        )

    def _resolve_exact(self, point: Point) -> tuple[str, str, str] | None:
        for item in self._country_shapes:
            iso2 = item["iso2"]
            if not iso2:
                continue

            try:
                if item["geom"].covers(point):
                    return iso2, item["name"], item.get("dataset", "boundary")
            except Exception:
                continue

        return None

    def _resolve_nearest(
        self,
        point: Point,
        lat: float,
        lon: float,
    ) -> tuple[str, str, float, str] | None:
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
                    candidates.append(
                        (
                            distance_deg,
                            iso2,
                            item["name"],
                            item.get("dataset", "boundary"),
                        )
                    )
            except Exception:
                continue

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        distance_deg, iso2, name, dataset = candidates[0]

        return iso2, name, distance_deg, dataset

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