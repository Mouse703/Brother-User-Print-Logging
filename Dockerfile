# Use official Python 3.11 slim image as base
FROM python:3.11-slim

# Install Firefox and required dependencies for Selenium with Firefox
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    curl \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver for Firefox
RUN GECKODRIVER_VERSION=v0.33.0 && \
    wget -q "https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz" && \
    tar -xzf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz -C /usr/local/bin && \
    rm geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz

# Set working directory
WORKDIR /app

# Copy your Python script into the container
COPY printlogging.py .

# Install Python dependencies
RUN pip install --no-cache-dir selenium paho-mqtt

# Use non-root user for safety
RUN useradd -m appuser
USER appuser

# Set environment variables defaults (can be overridden at runtime)
ENV DOWNLOADS_FOLDER=/downloads \
    DESTINATION_FOLDER=/logs

# Create folders with proper permissions
RUN mkdir -p /downloads /logs && chown appuser:appuser /downloads /logs

# Entrypoint to run your script
ENTRYPOINT ["python", "printlogging.py"]