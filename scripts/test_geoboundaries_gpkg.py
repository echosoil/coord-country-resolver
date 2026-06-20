from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point
from dotenv import load_dotenv

load_dotenv()

GPKG_PATH = Path("data/geoboundaries/geoBoundariesCGAZ_ADM0.gpkg")


def main():
    if not GPKG_PATH.exists():
        raise FileNotFoundError(f"Missing file: {GPKG_PATH}")

    print(f"Loading {GPKG_PATH} ...")
    world = gpd.read_file(GPKG_PATH, engine="pyogrio")

    print("Loaded rows:", len(world))
    print("CRS:", world.crs)
    print("Columns:", list(world.columns))

    # Ensure WGS84 lat/lon.
    if world.crs is not None and world.crs.to_epsg() != 4326:
        world = world.to_crs("EPSG:4326")

    tests = [
        (41.3874, 2.1686, "Barcelona"),
        (48.8566, 2.3522, "Paris"),
        (35.27595925977908, -2.9557758942246437, "XRXB-4454 / Melilla"),
    ]

    for lat, lon, label in tests:
        pt = Point(lon, lat)

        hits = world[world.geometry.covers(pt)]

        print()
        print(label)

        if hits.empty:
            print("No exact hit")
            continue

        # geoBoundaries commonly uses shapeGroup and shapeName.
        cols = [c for c in ["shapeGroup", "shapeName", "shapeType"] if c in hits.columns]
        print(hits[cols].to_string(index=False))


if __name__ == "__main__":
    main()