from dataclasses import asdict

from fastapi import FastAPI, HTTPException

from country_resolver import CountryResolver

app = FastAPI(
    title="Coordinate Country Resolver",
    version="0.1.0",
    description=(
        "Resolve latitude/longitude coordinate pairs to country codes. "
        "Boundary data may use geoBoundaries; see /attribution."
    ),
)

resolver = CountryResolver()

@app.get("/")
def root():
    return {
        "name": "coord-country-resolver",
        "description": "Resolve latitude/longitude coordinate pairs to country codes.",
        "docs": "/docs",
        "health": "/health",
        "attribution": "/attribution",
    }


@app.get("/attribution")
def attribution():
    return {
        "boundary_data": [
            {
                "name": "geoBoundaries",
                "website": "https://www.geoboundaries.org",
                "citation": (
                    "Runfola, D. et al. (2020) geoBoundaries: "
                    "A global database of political administrative boundaries. "
                    "PLoS ONE 15(4): e0231866. "
                    "https://doi.org/10.1371/journal.pone.0231866"
                ),
            },
            {
                "name": "Natural Earth",
                "website": "https://www.naturalearthdata.com",
            },
        ]
    }

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/resolve")
def resolve(lat: str, lon: str):
    try:
        result = resolver.resolve(lat, lon)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return asdict(result)