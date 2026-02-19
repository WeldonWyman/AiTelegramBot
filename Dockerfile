# Dockerfile for Telegram Media Downloader Bot
FROM python:3.12-slim

# Install ffmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bot.py .
COPY config_loader.py .
COPY cache_manager.py .
COPY downloader.py .
COPY queue_manager.py .

# Create directories for cache and logs
RUN mkdir -p /app/cache /app/logs

# Run the bot
CMD ["python", "-u", "bot.py"]
