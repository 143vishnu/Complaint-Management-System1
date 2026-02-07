# Backend Dockerfile - Compatible with Render
# Builds from repository root, runs from BE-main/

FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Set working directory to BE-main contents
WORKDIR /app

# Copy requirements.txt from BE-main directory
COPY BE-main/requirements.txt .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy all application files from BE-main
COPY BE-main/ .

# Expose port
EXPOSE 6969

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6969/api || exit 1

# Run the Flask application
CMD ["python", "server.py"]
