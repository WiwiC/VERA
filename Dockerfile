# Use Python 3.10 slim image
#FROM python:3.10-slim
FROM python:3.10.6-buster

# Set working directory
WORKDIR /app

# Install system dependencies
# ffmpeg: for audio/video processing
# libsndfile1: for librosa
# libgl1: for opencv (even headless sometimes needs it)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src src
COPY video-analyzer-app/ ./video-analyzer-app/
COPY .env .env

# ????? we dont have setup.py, should we??
# COPY setup.py setup.py

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Run the application
# Run the application
CMD uvicorn src.api.fast:app --host 0.0.0.0 --port 8080
