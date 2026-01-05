FROM python:3.12-slim-bookworm

# Get ARGS
ARG SECRET_KEY
ARG DATABASE_URL
ARG MEDIA_URL

# Set env vars
ENV SECRET_KEY=$SECRET_KEY \
    DATABASE_URL=$DATABASE_URL \
    MEDIA_URL=$MEDIA_URL \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Compiladores y herramientas de build
    gcc \
    g++ \
    make \
    cmake \
    pkg-config \
    # PostgreSQL
    postgresql-client \
    libpq-dev \
    # Pillow/imaging dependencies
    libjpeg-dev \
    libjpeg62-turbo \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    libwebp-dev \
    # Cairo dependencies (para pycairo)
    libcairo2-dev \
    libgirepository1.0-dev \
    # Python dev
    python3-dev \
    # Rust (si tienes paquetes que lo requieren)
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files (mejor que migrate en build time)
RUN python3 manage.py collectstatic --noinput || true

# Run the web service on container startup
CMD python3 manage.py migrate --noinput && \
    exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 config.wsgi:application