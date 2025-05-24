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

# First, install only the requirements to check for conflicts
RUN set -ex \
    && pip install --upgrade pip \
    && pip install -r requirements.txt --no-cache-dir || (pip check && false)

# Now build wheels with pinned versions to avoid conflicts
RUN set -ex \
    && pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt \
    && pip wheel --wheel-dir=/wheels --no-deps \
        pandasai==2.0.44 \
        openai==1.13.3 \
        matplotlib==3.8.2 \
        pandas==1.5.3 \
        httpx==0.28.1 \
        numpy>=1.24.0 \
        scipy>=1.10.0 \
        scikit-learn>=1.2.0 \
        python-multipart>=0.0.5 \
        python-jose[cryptography]>=3.3.0 \
        passlib[bcrypt]>=1.7.4 \
        pydantic>=1.10.2 \
        sqlalchemy>=1.4.0 \
        psycopg2-binary>=2.9.3 \
        alembic>=1.7.3 \
        python-dotenv>=0.19.0

# Final stage
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY Backend/requirements.txt .

# Verify requirements.txt exists and show its contents
RUN echo "Contents of requirements.txt:" && cat requirements.txt

# Install system dependencies first
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN set -ex \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir uvicorn[standard] \
    && pip install --no-cache-dir \
        pandasai==2.0.44 \
        openai==1.13.3 \
        pandas==1.5.3 \
        matplotlib==3.8.2 \
        scikit-learn>=1.2.0 \
        scipy>=1.10.0 \
        numpy>=1.24.0 \
        python-dotenv==1.0.0 \
    && pip check \
    && rm -rf /root/.cache/pip \
    && echo "Installed packages:" \
    && pip list

# Copy the rest of the application code
COPY Backend/ .

# Set the working directory to the Backend directory
WORKDIR /app/Backend

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Command to run the application using uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]

# List final directory contents for debugging
RUN echo "Final contents of /app/Backend:" && ls -la