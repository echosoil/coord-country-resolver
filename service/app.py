from dataclasses import asdict

from fastapi import FastAPI, HTTPException

from country_resolver import CountryResolver

app = FastAPI(
    title="Coordinate Country Resolver",
    version="0.1.0",
    description="Resolve latitude/longitude pairs to country codes.",
)

resolver = CountryResolver()


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