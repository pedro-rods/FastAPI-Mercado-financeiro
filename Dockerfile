# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# system deps (psycopg2 & backtrader need some)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Alembic migrations at container start (optional)
# You can also run it in entrypoint.sh if prefer
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
