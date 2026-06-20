import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResolverSettings:
    country_boundary_files: tuple[Path, ...]
    country_lookup_tolerance_deg: float = 0.10
    country_nearest_blacklist: frozenset[str] = frozenset()


def _split_paths(value: str) -> tuple[Path, ...]:
    return tuple(Path(x.strip()) for x in value.split(",") if x.strip())


def load_settings() -> ResolverSettings:
    raw_files = os.getenv("COUNTRY_BOUNDARY_FILES", "").strip()

    if raw_files:
        boundary_files = _split_paths(raw_files)
    else:
        # Backwards compatibility with the old single-shapefile setting.
        old_shp = os.getenv(
            "COUNTRY_SHP",
            "data/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp",
        )
        boundary_files = (Path(old_shp),)

    blacklist = frozenset(
        x.strip().upper()
        for x in os.getenv("COUNTRY_NEAREST_BLACKLIST", "").split(",")
        if x.strip()
    )

    return ResolverSettings(
        country_boundary_files=boundary_files,
        country_lookup_tolerance_deg=float(os.getenv("COUNTRY_LOOKUP_TOLERANCE_DEG", "0.10")),
        country_nearest_blacklist=blacklist,
    )