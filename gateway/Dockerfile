FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY gateway/ .

# Expose port
EXPOSE 8080

# Run the gateway
CMD ["python", "gateway.py"]
