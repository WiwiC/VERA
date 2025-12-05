#!/bin/bash

# Configuration
PROJECT_ID="vera-480211" # Replace with your actual Project ID if different
APP_NAME="vera-app"
REGION="europe-west1" # Choose your region

echo "🚀 Deploying $APP_NAME to Google Cloud Run..."

# 1. Build the image
echo "🔨 Building Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$APP_NAME .

# 2. Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy $APP_NAME \
    --image gcr.io/$PROJECT_ID/$APP_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2

echo "✅ Deployment complete!"
