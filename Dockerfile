# Simple single-stage build for faster Railway deployment
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy just the requirements file first
ADD ./Backend/requirements.txt .

# Debug - list all files to see what's here
RUN ls -la /app

# Install dependencies with prebuilt wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Debug - list files in the Backend directory
RUN ls -la /

# Copy the application code
ADD ./Backend .

# Debug - show final app structure
RUN ls -la /app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
