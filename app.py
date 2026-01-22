import streamlit as st
import os
import subprocess
from logic import download_audio, transcribe_audio, detect_events

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="AI Conversation Timeline",
    page_icon="⏱",
    layout="wide"
)

# --------------------------------------------------
# Language Mapping (Whisper code → Name)
# --------------------------------------------------
LANGUAGE_MAP = {
    "hi": "Hindi",
    "ml": "Malayalam",
    "en": "English",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ar": "Arabic"
}

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def ts(seconds):
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

def get_range(x, buf):
    return max(0, int(x - buf)), int(x + buf)

# --------------------------------------------------
# Download full video safely
# --------------------------------------------------
def download_full_video(url):
    os.makedirs("videos", exist_ok=True)
    path = "videos/source.mp4"

    if os.path.exists(path):
        return path

    cmd = [
        "yt-dlp",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "-o", path,
        url
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\n{result.stderr}")

    return path

# --------------------------------------------------
# Create video clip
# --------------------------------------------------
def create_clip(src, s, e, out):
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", str(s),
            "-i", src,
            "-t", str(e - s),
            "-c:v", "libx264",
            "-c:a", "aac",
            out
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

# --------------------------------------------------
# Session State
# --------------------------------------------------
for key in ["results", "video", "selected"]:
    if key not in st.session_state:
        st.session_state[key] = None

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.header("🔍 Video Analysis")

    url = st.text_input("YouTube URL")
    buffer = st.slider("Context Buffer (sec)", 10, 30, 15)

    if st.button("Analyze"):
        if not url:
            st.warning("Please enter a YouTube URL")
            st.stop()

        with st.spinner("Downloading audio..."):
            audio = download_audio(url)

        with st.spinner("Transcribing audio..."):
            segments = transcribe_audio(audio)

        with st.spinner("Detecting conversation events..."):
            st.session_state.results = detect_events(segments)

        with st.spinner("Downloading full video..."):
            try:
                st.session_state.video = download_full_video(url)
            except Exception as e:
                st.error(str(e))
                st.stop()

        os.remove(audio)
        st.success("Analysis complete!")

    if st.button("Reset"):
        st.session_state.clear()
        st.rerun()

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("## ⏱ Conversation Timeline Analyzer")
st.caption("Click an event to preview the exact video segment")

# --------------------------------------------------
# Layout
# --------------------------------------------------
left, center, right = st.columns([1.2, 2, 3])

# --------------------------------------------------
# Timeline Column
# --------------------------------------------------
with center:
    st.subheader("📍 Timeline")

    if st.session_state.results:
        for cat, label in [
            ("qa", "❓ Q&A"),
            ("agreement", "✅ Agreement"),
            ("disagreement", "⚡ Disagreement")
        ]:
            st.markdown(f"### {label}")
            for i, event in enumerate(st.session_state.results.get(cat, [])):
                start, end = get_range(event["start"], buffer)
                if st.button(
                    f"{ts(start)} → {ts(end)}",
                    key=f"{cat}_{i}"
                ):
                    st.session_state.selected = (cat, i)
    else:
        st.info("Run analysis to generate timeline")

# --------------------------------------------------
# Preview Panel
# --------------------------------------------------
with right:
    st.subheader("🎥 Preview")

    if st.session_state.selected:
        cat, i = st.session_state.selected
        event = st.session_state.results[cat][i]

        s, e_sec = get_range(event["start"], buffer)
        clip = f"clips/{cat}_{i}.mp4"
        os.makedirs("clips", exist_ok=True)

        if not os.path.exists(clip):
            create_clip(
                st.session_state.video,
                s,
                e_sec,
                clip
            )

        st.video(clip)

        st.markdown("**Transcript**")

        # Convert language code to readable name
        lang_code = event.get("original_language", "unknown")
        language = LANGUAGE_MAP.get(lang_code, lang_code)

        st.write(f"**Original Language:** {language}")
        st.write(f"**English (Translated):** {event['text']}")

    else:
        st.info("Select an event from the timeline")

# --------------------------------------------------
# Left Column (Empty for balance)
# --------------------------------------------------
with left:
    st.empty()
