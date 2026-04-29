# ---------- build stage ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools needed for some wheels (e.g. cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        pkg-config \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.11-slim

WORKDIR /app

# Install libssl at runtime (needed by cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from the build stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Gunicorn for production
RUN pip install --no-cache-dir gunicorn==22.0.0

ENV FLASK_APP=run.py \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "run:app"]
