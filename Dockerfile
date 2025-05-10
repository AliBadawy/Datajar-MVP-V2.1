FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt first for better caching
COPY Backend/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY Backend/ ./

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
