FROM python:3.10.6-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# system deps (common ones; add more if your requirements need them)
# ffmpeg: for audio/video processing
# libsndfile1: for librosa
# libgl1: for opencv (even headless sometimes needs it)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \ 
    libsndfile1 \
    libgl1 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "video-analyzer-app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
