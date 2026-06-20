import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResolverSettings:
    country_shp: Path
    country_lookup_tolerance_deg: float = 0.10
    country_nearest_blacklist: frozenset[str] = frozenset()


def load_settings() -> ResolverSettings:
    raw_shp = os.getenv(
        "COUNTRY_SHP",
        "data/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp",
    )

    blacklist = frozenset(
        x.strip().upper()
        for x in os.getenv("COUNTRY_NEAREST_BLACKLIST", "").split(",")
        if x.strip()
    )

    return ResolverSettings(
        country_shp=Path(raw_shp),
        country_lookup_tolerance_deg=float(
            os.getenv("COUNTRY_LOOKUP_TOLERANCE_DEG", "0.10")
        ),
        country_nearest_blacklist=blacklist,
    )