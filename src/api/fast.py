from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from pathlib import Path
from src.main import run_pipelines

app = FastAPI()

# Allow all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to VERA API! Use /analyze to upload a video."}

@app.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    """
    Upload a video file, run the VERA analysis pipeline, and return the results.
    """
    # 1. Save uploaded file temporarily
    temp_dir = Path("data/raw")
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_video_path = temp_dir / file.filename

    try:
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    # 2. Run Analysis Pipeline
    try:
        # run_pipelines returns (output_dir, results_dict)
        output_dir, results = run_pipelines(str(temp_video_path))

        # 3. Return Results
        return {
            "status": "success",
            "filename": file.filename,
            "results": results
        }
    except Exception as e:
        # Clean up if possible
        if temp_video_path.exists():
            os.remove(temp_video_path)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
