"""
Core extraction logic for the VERA Audio Module.
Extracts raw features using Whisper, Librosa, and WebRTCVAD.
"""

import os
import numpy as np
import librosa
import soundfile as sf
import webrtcvad
import pyloudnorm as pyln
from faster_whisper import WhisperModel
from moviepy import VideoFileClip
from pathlib import Path

def extract_audio_from_video(video_path, output_dir):
    """
    Extract audio track from video file to .mp3.
    """
    video_path = Path(video_path)
    output_path = Path(output_dir) / f"{video_path.stem}.mp3"

    if output_path.exists():
        return str(output_path)

    try:
        video = VideoFileClip(str(video_path))
        video.audio.write_audiofile(str(output_path), codec='mp3', bitrate='192k', logger=None)
        video.close()
        return str(output_path)
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None

def get_transcription(audio_path):
    """
    Run Whisper to get WPM and text.
    """
    try:
        model = WhisperModel("small", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path, beam_size=1)

        words = 0
        first_t = None
        last_t = None

        for seg in segments:
            text = seg.text.strip()
            if not text: continue

            words += len(text.split())
            if first_t is None: first_t = seg.start
            last_t = seg.end

        if words > 0 and last_t is not None and first_t is not None:
            duration_min = (last_t - first_t) / 60.0
            wpm = words / max(duration_min, 1e-6)
        else:
            wpm = 0.0

        return wpm
    except Exception as e:
        print(f"Error in transcription: {e}")
        return 0.0

def get_pitch_metrics(y, sr):
    """
    Extract Pitch Mean (Hz) and Pitch Std (Semitones).
    """
    try:
        # Use pyin for F0 estimation
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr
        )
        f0_voiced = f0[~np.isnan(f0)]

        if len(f0_voiced) == 0:
            return 0.0, 0.0

        # Mean Hz (Context)
        mean_hz = float(np.mean(f0_voiced))

        # Std Semitones (Performance)
        # Convert Hz to Semitones relative to the mean
        # Formula: 12 * log2(f / ref)
        semitones = 12 * np.log2(f0_voiced / mean_hz)
        std_st = float(np.std(semitones))

        return mean_hz, std_st
    except Exception as e:
        print(f"Error in pitch metrics: {e}")
        return 0.0, 0.0

def get_volume_metrics(y, sr):
    """
    Extract Volume Mean (LUFS), CV, and Crest Factor.
    """
    try:
        # 1. LUFS (Context)
        meter = pyln.Meter(sr)
        lufs = float(meter.integrated_loudness(y))

        # 2. RMS Metrics (Performance)
        frame_len = int(0.05 * sr)
        hop_len = frame_len // 2
        rms = librosa.feature.rms(y=y, frame_length=frame_len, hop_length=hop_len)[0]

        # Filter silence for CV calculation
        # Use 1% of peak RMS as silence threshold to avoid inflating variance with zeros
        threshold = 0.01 * (np.max(rms) + 1e-9)
        rms_active = rms[rms > threshold]

        if len(rms_active) == 0:
            rms_active = rms # Fallback if everything is silent

        rms_mean = float(np.mean(rms_active))
        rms_std = float(np.std(rms_active))
        cv = rms_std / (rms_mean + 1e-9)

        # 3. Crest Factor (Energy)
        peak = float(np.max(np.abs(y)))
        overall_rms = float(np.sqrt(np.mean(y**2)))
        if overall_rms > 1e-9:
            crest_db = 20 * np.log10(peak / overall_rms)
        else:
            crest_db = 0.0

        return lufs, cv, crest_db
    except Exception as e:
        print(f"Error in volume metrics: {e}")
        return -70.0, 0.0, 0.0

def get_pause_metrics(y, sr):
    """
    Extract Pause Ratio using WebRTCVAD.
    """
    try:
        vad = webrtcvad.Vad(2) # Mode 2: Aggressive

        # Resample to 16kHz for VAD if needed (handled in main process)
        # Frame size must be 10, 20, or 30ms. Let's use 30ms.
        frame_ms = 30
        frame_len = int(sr * frame_ms / 1000)
        num_frames = len(y) // frame_len

        # Convert to 16-bit PCM
        pcm = (y * 32767).astype(np.int16).tobytes()

        speech_frames = 0
        for i in range(num_frames):
            start = i * frame_len * 2
            end = start + frame_len * 2
            frame = pcm[start:end]

            if len(frame) < frame_len * 2: break

            if vad.is_speech(frame, sr):
                speech_frames += 1

        total_duration = len(y) / sr
        speech_duration = speech_frames * frame_ms / 1000.0
        pause_duration = total_duration - speech_duration

        return max(pause_duration, 0.0) / max(total_duration, 1e-6)
    except Exception as e:
        print(f"Error in pause metrics: {e}")
        return 0.0

def process_audio(video_path, output_dir):
    """
    Main extraction function.
    """
    # 1. Extract Audio File
    audio_path = extract_audio_from_video(video_path, output_dir)
    if not audio_path:
        return {}

    # 2. Load Audio (16kHz mono for consistency)
    y, sr = sf.read(audio_path)
    if y.ndim > 1: y = np.mean(y, axis=1)
    if sr != 16000:
        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
        sr = 16000

    # 3. Run Extractors
    wpm = get_transcription(audio_path)
    mean_hz, std_st = get_pitch_metrics(y, sr)
    lufs, cv, crest_db = get_volume_metrics(y, sr)
    pause_ratio = get_pause_metrics(y, sr)

    return {
        "wpm": wpm,
        "pause_ratio": pause_ratio,
        "pitch_mean_hz": mean_hz,
        "pitch_std_st": std_st,
        "volume_lufs": lufs,
        "volume_cv": cv,
        "crest_factor_db": crest_db
    }
