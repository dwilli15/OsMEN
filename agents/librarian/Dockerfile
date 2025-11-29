# OsMEN Librarian - Dockerfile
# Semantic Memory & Lateral Thinking RAG Engine

FROM python:3.12-slim

LABEL maintainer="OsMEN Project"
LABEL description="Librarian RAG Engine for OsMEN"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data /app/data/db /app/data/sources

# Create non-root user for security
RUN useradd -m -u 1000 librarian && \
    chown -R librarian:librarian /app

USER librarian

# Expose the API port
EXPOSE 8200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8200/health || exit 1

# Start the API server
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8200"]
