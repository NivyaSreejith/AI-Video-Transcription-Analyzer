import whisper
import yt_dlp
import os
import uuid
import subprocess

# --------------------------------------------------
# FFmpeg Configuration (GLOBAL)
# --------------------------------------------------
FFMPEG_DIR = r"C:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin"
os.environ["PATH"] += os.pathsep + FFMPEG_DIR
os.environ["FFMPEG_BINARY"] = os.path.join(FFMPEG_DIR, "ffmpeg.exe")

# --------------------------------------------------
# Load Whisper Small Model (once)
# --------------------------------------------------
model = whisper.load_model("small")

# --------------------------------------------------
# Download Audio Only (for Transcription)
# --------------------------------------------------
def download_audio(youtube_url):
    uid = str(uuid.uuid4())
    output_template = f"audio_{uid}.%(ext)s"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    for file in os.listdir("."):
        if file.startswith(f"audio_{uid}") and file.endswith(".mp3"):
            return file

    raise FileNotFoundError("Audio download failed.")

# --------------------------------------------------
# Transcription (Multilingual → English)
# --------------------------------------------------
def transcribe_audio(audio_path):
    result = model.transcribe(
        audio_path,
        task="translate"  # Automatically translates to English
    )
    language = result.get("language", "unknown")  # Detected original language
    segments = result["segments"]

    # Store detected language for each segment
    for seg in segments:
        seg["original_language"] = language

    return segments

# --------------------------------------------------
# Event Detection (based on English text)
# --------------------------------------------------
def detect_events(segments):
    results = {
        "qa": [],
        "agreement": [],
        "disagreement": []
    }

    for seg in segments:
        text = seg["text"].lower()

        # Question detection
        if "?" in text or any(w in text for w in ["what", "why", "how", "when", "do you", "are you"]):
            results["qa"].append(seg)

        # Agreement detection
        if any(w in text for w in ["yes", "exactly", "right", "agree", "correct"]):
            results["agreement"].append(seg)

        # Disagreement detection
        if any(w in text for w in ["no", "not true", "disagree", "but", "however"]):
            results["disagreement"].append(seg)

    return results
