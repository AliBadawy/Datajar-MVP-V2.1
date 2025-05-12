FROM python:3.9-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for building wheels
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker caching
# Railway build context starts from the repository root
COPY Backend/requirements.txt .

# Use binary wheels where possible - critical for pandas/scipy
ENV PIP_ONLY_BINARY=numpy,pandas,scipy,matplotlib

# Install dependencies into the /build directory
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

# Start a clean image for the final application
FROM python:3.9-slim

# Copy wheels from builder stage
WORKDIR /app
COPY --from=builder /wheels /wheels

# Install dependencies from pre-built wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels

# Copy application code - from the repository root
COPY Backend/ .

# Set environment variables
ENV PORT=8000

# Set the command to run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
