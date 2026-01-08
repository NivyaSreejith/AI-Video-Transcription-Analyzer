import whisper
import yt_dlp
import os
import uuid


ffmpeg_path = r"C:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin"
os.environ["PATH"] += os.pathsep + ffmpeg_path
os.environ["FFMPEG_BINARY"] = os.path.join(ffmpeg_path, "ffmpeg.exe")

# Load Whisper model
model = whisper.load_model("base")



# Download YouTube audio

def download_audio(youtube_url):
    uid = str(uuid.uuid4())
    output_template = os.path.join(os.getcwd(), f"audio_{uid}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "ffmpeg_location": ffmpeg_path,
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

    # Find the downloaded MP3 file
    for file in os.listdir("."):
        if file.startswith(f"audio_{uid}") and file.endswith(".mp3"):
            return os.path.join(os.getcwd(), file)

    raise FileNotFoundError("Audio download failed.")



# Transcribe audio with Whisper

def transcribe_audio(audio_path):
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    result = model.transcribe(audio_path)
    return result["segments"]


# Detect Q&A, Agreement, Disagreement

def detect_events(segments):
    results = {"qa": [], "agreement": [], "disagreement": []}

    for seg in segments:
        text = seg["text"].lower()

        # Questions
        if "?" in text:
            results["qa"].append(seg)

        # Agreement
        if any(w in text for w in ["yes", "exactly", "right", "agree"]):
            results["agreement"].append(seg)

        # Disagreement
        if any(w in text for w in ["no", "not true", "disagree", "but"]):
            results["disagreement"].append(seg)

    return results
