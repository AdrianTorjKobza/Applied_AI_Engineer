FROM python3.11-slim

WORKDIR app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app .app

# Set Python path so it finds the app modules
ENV PYTHONPATH=app

# Expose port and run Uvicorn
EXPOSE 8000
CMD [uvicorn, app.mainapp, --host, 0.0.0.0, --port, 8000]