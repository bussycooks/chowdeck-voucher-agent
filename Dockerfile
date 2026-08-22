FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    apt-transport-https \
    ca-certificates \
    chromium \
    firefox \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium firefox

# Copy application code
COPY app/ ./app/
COPY tests/ ./tests/

# Create necessary directories
RUN mkdir -p ./browser_profiles ./logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_MODE=production

# Run the application
CMD ["python", "-m", "app.main"]
