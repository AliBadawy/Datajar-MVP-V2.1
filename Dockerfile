# Direct build for Railway with explicit paths
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements directly from the Backend directory in the repo
COPY Backend/requirements.txt /app/

# List current directory contents for debugging
RUN echo "Contents of /app:" && ls -la /app

# Install dependencies 
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire Backend directory to the app directory
COPY Backend/ /app/

# List final directory contents for debugging
RUN echo "Final contents of /app:" && ls -la /app

# Expose port
EXPOSE 8000

# Run the application (shell form to allow environment variable expansion)
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
