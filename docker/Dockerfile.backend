FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code and all project root folders
COPY backend /app/backend
COPY ai /app/ai
COPY models /app/models
COPY services /app/services
COPY routes /app/routes
COPY database /app/database
COPY authentication /app/authentication
COPY utils /app/utils

# Ensure static asset and log directories exist
RUN mkdir -p /app/static/uploads /app/static/heatmaps /app/static/annotations /app/static/reports /app/logs

EXPOSE 8000

ENV PYTHONPATH=/app
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
