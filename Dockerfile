# Multi-stage build for Railway
FROM python:3.9-slim AS builder

# Set environment variables for optimal build performance
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

# Copy requirements first to leverage Docker caching
COPY Backend/requirements.txt .

# Use binary wheels where possible - critical for pandas/scipy
ENV PIP_ONLY_BINARY=numpy,pandas,scipy,matplotlib

# Build wheels for all dependencies
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

# Explicitly build wheels for PandasAI and its dependencies
RUN pip wheel --no-cache-dir --wheel-dir=/wheels pandasai==2.0.44 openai==1.13.3 matplotlib==3.8.2 pandas==1.5.3

# Start a clean image for the final application
FROM python:3.9-slim

# Copy wheels from builder stage
WORKDIR /app
COPY --from=builder /wheels /wheels

# Install dependencies from pre-built wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels
    
# List installed packages for debugging
RUN pip list

# Explicitly verify PandasAI and OpenAI are installed
RUN pip show pandasai && pip show openai

# Copy the entire Backend directory to the app directory
COPY Backend/ /app/

# List final directory contents for debugging
RUN echo "Final contents of /app:" && ls -la /app

# Expose port
EXPOSE 8000

# Run the application (shell form to allow environment variable expansion)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
