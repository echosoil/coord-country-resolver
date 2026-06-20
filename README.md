# Coordinate Country Resolver

`coord-country-resolver` is a small Python library and FastAPI service for resolving latitude/longitude coordinate pairs to country codes using administrative boundary polygons.

It was developed for the ECHO / ECHOREPO data infrastructure to support validation and enrichment of citizen-generated soil sampling records.

## Features

- Resolve latitude/longitude coordinates to ISO-2 country codes.
- Supports multiple boundary datasets in priority order.
- Supports GeoPackage (`.gpkg`) and Shapefile (`.shp`) boundary files.
- Uses exact polygon matching first.
- Uses nearest-polygon fallback within a configurable tolerance.
- Falls back to `reverse_geocoder` if polygon lookup fails.
- Provides both a Python API and a FastAPI HTTP service.
- Docker-ready.

## Boundary data

The resolver does not commit boundary datasets to the repository. You must download them separately.

Recommended setup:

1. geoBoundaries CGAZ ADM0 GeoPackage as the primary boundary dataset.
2. Natural Earth ADM0 Shapefile as a fallback dataset.

Example local file layout:

```text
data/
  geoboundaries/
    geoBoundariesCGAZ_ADM0.gpkg
  ne_50m_admin_0_countries/
    ne_50m_admin_0_countries.shp
    ne_50m_admin_0_countries.shx
    ne_50m_admin_0_countries.dbf

## License

The source code in this repository is licensed under the Apache License 2.0.

Documentation and repository text are licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0), unless otherwise stated.

Boundary data files are not included in this repository. If you configure the resolver to use geoBoundaries data, you must follow geoBoundaries attribution requirements.

See [NOTICE](NOTICE) and [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md).