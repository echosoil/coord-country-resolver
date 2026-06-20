from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from country_resolver import CountryResolver


class CoordinatePoint(BaseModel):
    id: str | None = Field(default=None, description="Optional caller-provided identifier")
    lat: Any = Field(..., description="Latitude")
    lon: Any = Field(..., description="Longitude")


class ResolveBatchRequest(BaseModel):
    points: list[CoordinatePoint]


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
        "resolve": "/resolve",
        "resolve_batch": "/resolve-batch",
        "attribution": "/attribution",
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


@app.post("/resolve-batch")
def resolve_batch(payload: ResolveBatchRequest):
    """
    Resolve many coordinate pairs in one API call.

    Each input point may contain an optional `id`, which is returned unchanged
    so callers can match results back to their own rows/samples.
    """
    results = []

    try:
        for point in payload.points:
            result = resolver.resolve(point.lat, point.lon)
            item = asdict(result)
            item["id"] = point.id
            results.append(item)

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {
        "count": len(results),
        "results": results,
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