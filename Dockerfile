FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Add a timestamp comment to invalidate cache
# Update: 2025-05-10 18:57

# Copy requirements.txt first for better caching
COPY Backend/requirements.txt ./

# Install dependencies with version verification
RUN pip install --no-cache-dir -r requirements.txt && \
    pip freeze | grep pandasai

# Copy the rest of the backend code
COPY Backend/ ./

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
