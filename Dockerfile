# ==============================================================================
# Sturdy IDP Engine - Dockerfile (Production Ready)
# Multi-stage optimized build for Python 3.12 with Poppler & ZBar
# ==============================================================================
FROM python:3.12-slim-bookworm AS base

# Install system utilities & binary dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libzbar0 \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-ind \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Ensure storage directories exist
RUN mkdir -p /app/storage/temp

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/stats || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
