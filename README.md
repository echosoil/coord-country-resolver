# Coordinate Country Resolver

`coord-country-resolver` is a small Python library and FastAPI service for resolving latitude/longitude coordinate pairs to ISO-2 country codes using administrative boundary polygons.

It was developed for the ECHO / ECHOREPO data infrastructure to support validation and enrichment of citizen-generated soil sampling records.

The resolver supports multiple boundary datasets in priority order. A typical configuration uses:

1. **geoBoundaries CGAZ ADM0 GeoPackage** as the primary boundary dataset.
2. **Natural Earth ADM0 Shapefile** as a fallback dataset.
3. A nearest-polygon fallback controlled by `COUNTRY_LOOKUP_TOLERANCE_DEG`.
4. A final `reverse_geocoder` fallback if polygon lookup fails.

Boundary data files are **not included** in this repository and must be downloaded separately.

---

## Features

* Resolve latitude/longitude coordinates to ISO-2 country codes.
* Supports multiple boundary files in priority order.
* Supports GeoPackage (`.gpkg`) and Shapefile (`.shp`) boundary formats.
* Uses exact polygon matching first.
* Uses nearest-polygon fallback within a configurable tolerance.
* Falls back to `reverse_geocoder` when polygon lookup fails.
* Provides both a Python API and a FastAPI HTTP API.
* Docker-ready.
* Designed for integration into ECHOREPO / EchoSoil data validation workflows.

---

## Repository structure

```text
coord-country-resolver/
├── country_resolver/
│   ├── __init__.py
│   ├── models.py
│   ├── resolver.py
│   └── settings.py
├── service/
│   ├── __init__.py
│   └── app.py
├── scripts/
│   ├── smoke_test.py
│   ├── smoke_test_api.py
│   └── test_geoboundaries_gpkg.py
├── tests/
│   └── test_resolver.py
├── data/
│   └── .gitkeep
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── .gitignore
├── .dockerignore
├── ACKNOWLEDGEMENTS.md
├── CITATION.cff
├── NOTICE
└── README.md
```

The `data/` directory is used for local boundary datasets but the actual boundary files are ignored by Git.

---

## Boundary data

This repository does not include boundary data files.

Recommended local layout:

```text
data/
├── geoboundaries/
│   └── geoBoundariesCGAZ_ADM0.gpkg
└── ne_50m_admin_0_countries/
    ├── ne_50m_admin_0_countries.shp
    ├── ne_50m_admin_0_countries.shx
    ├── ne_50m_admin_0_countries.dbf
    ├── ne_50m_admin_0_countries.prj
    └── ne_50m_admin_0_countries.cpg
```

### geoBoundaries

Download the **CGAZ ADM0 GeoPackage** from geoBoundaries global downloads.

Recommended local path:

```text
data/geoboundaries/geoBoundariesCGAZ_ADM0.gpkg
```

### Natural Earth

Download the **Admin 0 Countries** Shapefile from Natural Earth.

Recommended local path:

```text
data/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp
```

The Shapefile must be kept together with its companion files, especially `.shx` and `.dbf`.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/echosoil/coord-country-resolver.git
cd coord-country-resolver
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the package in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

If you use the shared ECHOREPO virtual environment instead:

```bash
cd ~/ECHO-STORE/coord-country-resolver
source ../venv/bin/activate
pip install -e ".[dev]"
```

---

## Configuration

Create a local `.env` file:

```bash
cp .env.example .env
```

Example local `.env`:

```env
COUNTRY_BOUNDARY_FILES=data/geoboundaries/geoBoundariesCGAZ_ADM0.gpkg,data/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp
COUNTRY_LOOKUP_TOLERANCE_DEG=0.10
COUNTRY_NEAREST_BLACKLIST=
LOG_LEVEL=INFO
```

The order of `COUNTRY_BOUNDARY_FILES` matters.

For example:

```env
COUNTRY_BOUNDARY_FILES=data/geoboundaries/geoBoundariesCGAZ_ADM0.gpkg,data/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp
```

means:

1. Try geoBoundaries first.
2. If no exact geoBoundaries match exists, try Natural Earth.
3. If no exact match exists in any configured boundary file, try nearest-polygon fallback.
4. If that fails, try `reverse_geocoder`.

---

## Environment variables

| Variable                       | Description                                                                             | Example                                                                                                     |
| ------------------------------ | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `COUNTRY_BOUNDARY_FILES`       | Comma-separated list of boundary files, in priority order. Supports `.gpkg` and `.shp`. | `data/geoboundaries/geoBoundariesCGAZ_ADM0.gpkg,data/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp` |
| `COUNTRY_LOOKUP_TOLERANCE_DEG` | Maximum distance in degrees for nearest-polygon fallback.                               | `0.10`                                                                                                      |
| `COUNTRY_NEAREST_BLACKLIST`    | Optional comma-separated ISO-2 country codes to ignore during nearest-polygon fallback. | `AQ`                                                                                                        |
| `LOG_LEVEL`                    | Logging level.                                                                          | `INFO`                                                                                                      |

Older versions used `COUNTRY_SHP`. The current preferred setting is `COUNTRY_BOUNDARY_FILES`.

---

## Resolution logic

For each coordinate pair, the resolver performs the following steps:

1. Parse and validate latitude and longitude.
2. Load configured boundary files if not already loaded.
3. Try exact polygon matching in the order defined by `COUNTRY_BOUNDARY_FILES`.
4. If no exact match exists, search for the nearest polygon within `COUNTRY_LOOKUP_TOLERANCE_DEG`.
5. If no polygon match exists, use `reverse_geocoder`.
6. If all methods fail, return an unresolved result.

Example result for an exact match:

```json
{
  "lat": 41.3874,
  "lon": 2.1686,
  "country_code": "ES",
  "country_source": "geoboundaries_exact",
  "country_lookup_note": "",
  "distance_deg": 0.0,
  "matched_country_name": "Spain"
}
```

Example result for a nearest fallback:

```json
{
  "lat": 42.0,
  "lon": 3.0,
  "country_code": "ES",
  "country_source": "geoboundaries_nearest",
  "country_lookup_note": "nearest_polygon_within_tolerance",
  "distance_deg": 0.034,
  "matched_country_name": "Spain"
}
```

Example result for invalid coordinates:

```json
{
  "lat": null,
  "lon": 2.0,
  "country_code": "",
  "country_source": "",
  "country_lookup_note": "invalid_or_missing_coordinates",
  "distance_deg": null,
  "matched_country_name": ""
}
```

---

## Python usage

```python
from dotenv import load_dotenv

from country_resolver import CountryResolver

load_dotenv()

resolver = CountryResolver()

result = resolver.resolve(41.3874, 2.1686)

print(result.country_code)
print(result.country_source)
print(result.matched_country_name)
```

Expected output:

```text
ES
geoboundaries_exact
Spain
```

---

## Local smoke test

Run:

```bash
python3 scripts/smoke_test.py
```

Typical output:

```text
Barcelona
country_code: ES
source: geoboundaries_exact
note:
matched: Spain
distance_deg: 0.0

Paris
country_code: FR
source: geoboundaries_exact
note:
matched: France
distance_deg: 0.0

XRXB-4454 / Melilla
country_code: ES
source: geoboundaries_exact
note:
matched: Spain
distance_deg: 0.0

bad input
country_code:
source:
note: invalid_or_missing_coordinates
matched:
distance_deg: None
```

The exact output may differ depending on which boundary datasets are configured.

To check which boundary datasets are actually loaded:

```bash
python3 - <<'PY'
from collections import Counter
from dotenv import load_dotenv

from country_resolver import CountryResolver

load_dotenv()

resolver = CountryResolver()
resolver.load()

print(Counter(x["dataset"] for x in resolver._country_shapes))
PY
```

Expected output should include both `geoboundaries` and `naturalearth` if both datasets are configured:

```text
Counter({'geoboundaries': ..., 'naturalearth': ...})
```

---

## FastAPI service

Run the API locally:

```bash
uvicorn service.app:app --host 0.0.0.0 --port 8010
```

Open the interactive API documentation:

```text
http://127.0.0.1:8010/docs
```

### Health check

```bash
curl "http://127.0.0.1:8010/health"
```

Expected response:

```json
{
  "status": "ok"
}
```

### Resolve coordinates

```bash
curl "http://127.0.0.1:8010/resolve?lat=41.3874&lon=2.1686"
```

Example response:

```json
{
  "lat": 41.3874,
  "lon": 2.1686,
  "country_code": "ES",
  "country_source": "geoboundaries_exact",
  "country_lookup_note": "",
  "distance_deg": 0.0,
  "matched_country_name": "Spain"
}
```

### Attribution endpoint

```bash
curl "http://127.0.0.1:8010/attribution"
```

This endpoint exposes boundary data attribution information.

---

## API smoke test

Start the API first:

```bash
uvicorn service.app:app --host 0.0.0.0 --port 8010
```

In another terminal, run:

```bash
python3 scripts/smoke_test_api.py
```

This tests `/health` and several `/resolve` calls.

---

## Docker usage

The Docker service expects boundary files to be available under the local `data/` directory and mounts them into the container as `/data`.

Docker Compose uses container paths:

```env
COUNTRY_BOUNDARY_FILES=/data/geoboundaries/geoBoundariesCGAZ_ADM0.gpkg,/data/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp
```

Build and start the service:

```bash
docker compose up -d --build
```

Check status:

```bash
docker ps
```

Check logs:

```bash
docker logs -f coord-country-resolver
```

Test the API:

```bash
curl "http://127.0.0.1:8010/health"
curl "http://127.0.0.1:8010/resolve?lat=41.3874&lon=2.1686"
```

Stop the service:

```bash
docker compose down
```

Rebuild after code changes:

```bash
docker compose down
docker compose up -d --build
```

---

## Docker troubleshooting

### Check that data is visible inside the container

```bash
docker exec -it coord-country-resolver sh -lc '
ls -lah /data
ls -lah /data/geoboundaries
ls -lah /data/ne_50m_admin_0_countries
'
```

### Check API health from inside the container

```bash
docker exec -it coord-country-resolver sh -lc '
curl -fsS http://127.0.0.1:8010/health
'
```

### Check configured environment variables inside the container

```bash
docker exec -it coord-country-resolver sh -lc '
env | grep COUNTRY
'
```

---

## Tests

Run Python syntax check:

```bash
python3 -m py_compile country_resolver/resolver.py
python3 -m py_compile country_resolver/settings.py
python3 -m py_compile service/app.py
```

Run smoke tests:

```bash
python3 scripts/smoke_test.py
```

Run API smoke test:

```bash
uvicorn service.app:app --host 0.0.0.0 --port 8010
python3 scripts/smoke_test_api.py
```

Run unit tests:

```bash
pytest
```

Run Ruff checks:

```bash
ruff check .
```

---

## Git hygiene

Boundary data and generated files should not be committed.

Recommended `.gitignore` entries:

```gitignore
# Boundary data
data/geoboundaries/
data/ne_*/
*.gpkg
*.shp
*.shx
*.dbf
*.prj
*.cpg

# Python generated files
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
build/
dist/

# Local environments
.venv/
venv/
env/
.env

# Tool caches
.pytest_cache/
.ruff_cache/
```

Check that no boundary data or generated egg-info files are tracked:

```bash
git ls-files | grep -E "egg-info|data/geoboundaries|data/ne_|\.gpkg|\.shp|\.shx|\.dbf"
```

Expected result: no output.

If generated files were already committed, remove them from Git tracking but keep them locally:

```bash
git rm -r --cached coord_country_resolver.egg-info
git rm -r --cached data/geoboundaries data/ne_50m_admin_0_countries
```

Then commit the cleanup:

```bash
git commit -m "Remove generated and local boundary data files"
git push
```

---

## Acknowledgements

When configured with geoBoundaries CGAZ ADM0 data, this project uses boundary data from [geoBoundaries](https://www.geoboundaries.org).

Recommended citation:

Runfola, D. et al. (2020) geoBoundaries: A global database of political administrative boundaries. *PLoS ONE* 15(4): e0231866. https://doi.org/10.1371/journal.pone.0231866

This project may also use Natural Earth boundary data as a fallback dataset:

Natural Earth: https://www.naturalearthdata.com

See [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md) and [NOTICE](NOTICE).

---

## License

The source code in this repository is licensed under the Apache License 2.0, unless otherwise stated.

Documentation and repository text are licensed under the Creative Commons Attribution 4.0 International License, CC BY 4.0, unless otherwise stated.

Boundary data files are not included in this repository. Users are responsible for downloading external boundary datasets and complying with their license and attribution requirements.

---

## Suggested GitHub description

```text
Resolve latitude/longitude coordinates to country codes using geoBoundaries, Natural Earth, and FastAPI.
```

Suggested GitHub topics:

```text
geospatial
geoboundaries
natural-earth
fastapi
gis
country-codes
coordinate-resolution
echosoil
echorepo
horizon-europe
```
