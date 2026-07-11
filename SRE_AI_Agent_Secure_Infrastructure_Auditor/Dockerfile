# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for cryptography and networking
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ /app/src/

# Change working directory to where the code lives
WORKDIR /app/src

# We don't use ENTRYPOINT directly here because we need Vault to intercept the boot sequence
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]