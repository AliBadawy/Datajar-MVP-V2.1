# Multi-stage build for Railway
FROM python:3.9-slim AS builder

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.4.2

# Set working directory
WORKDIR /app

# Install system dependencies in a single layer
RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY Backend/requirements.txt .

# Create directory for wheels
RUN mkdir /wheels

# Build wheels for all dependencies in one layer
RUN set -ex \
    && pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt \
    && pip wheel --no-cache-dir --wheel-dir=/wheels pandasai==2.0.44 openai==1.13.3 matplotlib==3.8.2 pandas==1.5.3 httpx==0.28.1

# Final stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies in a single layer
RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /wheels /wheels

# Install from wheels and clean up in one layer
RUN set -ex \
    && pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels \
    && rm -rf /root/.cache/pip

# Copy application code
COPY Backend/ .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

# Expose the port the app runs on
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Command to run the application using uvicorn with auto-reload in development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT}", "--proxy-headers"]

# List final directory contents for debugging
RUN echo "Final contents of /app:" && ls -la /app
