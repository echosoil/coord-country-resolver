FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies useful for shapely/pyshp wheels and runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY country_resolver ./country_resolver
COPY service ./service

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

ENV COUNTRY_SHP=/data/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp
ENV COUNTRY_LOOKUP_TOLERANCE_DEG=0.10
ENV COUNTRY_NEAREST_BLACKLIST=
ENV LOG_LEVEL=INFO

EXPOSE 8010

CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8010"]