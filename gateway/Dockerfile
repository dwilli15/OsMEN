FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy gateway application
COPY gateway/ ./gateway/

# Copy integrations module (needed for paths, memory, oauth)
COPY integrations/ ./integrations/

# Set Python path so integrations can be imported
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Run the gateway from gateway subdirectory
CMD ["python", "gateway/gateway.py"]
