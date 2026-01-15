import streamlit as st
import os
from logic import (
    fetch_audio_stream as download_audio,
    convert_speech_to_text as transcribe_audio,
    extract_conversation_insights as detect_events
)

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="Video Insight Explorer",
    layout="wide",
    page_icon="🎥"
)

# -------------------------------------------------
# Custom CSS Styling
# -------------------------------------------------
st.markdown("""
<style>
    body { background-color: #0f172a; }
    .main { background-color: #0f172a; color: #e5e7eb; }
    .hero {
        background: linear-gradient(90deg, #1e293b, #020617);
        padding: 2rem; border-radius: 18px; margin-bottom: 1.5rem;
    }
    .hero h1 { color: #f8fafc; font-size: 2.4rem; }
    .hero p { color: #cbd5f5; font-size: 1.1rem; }
    .card {
        background-color: #020617; border-radius: 16px;
        padding: 1.2rem; margin-bottom: 1rem;
        box-shadow: 0 0 12px rgba(99,102,241,0.15);
    }
    .tag { color: #a5b4fc; font-size: 0.9rem; }
    .footer { text-align: center; color: #94a3b8; margin-top: 3rem; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def format_timestamp(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def get_context_range(x_seconds: float, buffer_seconds: int):
    start = max(0, int(x_seconds - buffer_seconds))
    end = int(x_seconds + buffer_seconds)
    return format_timestamp(start), format_timestamp(end)

def get_video_id(url: str) -> str:
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return ""

def mmss_to_seconds(mmss: str) -> int:
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)

# -------------------------------------------------
# Session State
# -------------------------------------------------
if "current_video" not in st.session_state:
    st.session_state.current_video = None
if "results" not in st.session_state:
    st.session_state.results = None

# -------------------------------------------------
# Hero Header
# -------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>🎬 Video Insight Explorer</h1>
    <p>
        Discover <b>Q&A moments</b>, <b>agreements</b>, and <b>conflicts</b>
        hidden inside YouTube videos using AI-powered audio intelligence.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Sidebar Controls
# -------------------------------------------------
with st.sidebar:
    st.header("🎛️ Control Panel")
    youtube_url = st.text_input("🔗 Paste YouTube Link", placeholder="https://www.youtube.com/watch?v=...")
    buffer_seconds = st.slider("⏱️ Context Window (seconds)", 5, 40, 20)
    st.markdown("---")
    analyze_btn = st.button("🚀 Run Analysis")
    clear_btn = st.button("🧹 Reset App")

# -------------------------------------------------
# Clear State
# -------------------------------------------------
if clear_btn:
    st.session_state.current_video = None
    st.session_state.results = None
    st.experimental_rerun()

# -------------------------------------------------
# Analyze Video
# -------------------------------------------------
if analyze_btn and youtube_url:
    if st.session_state.current_video != youtube_url:
        st.session_state.current_video = youtube_url
        st.session_state.results = None

    with st.spinner("📥 Fetching audio stream..."):
        audio_path = download_audio(youtube_url)

    with st.spinner("🧠 Converting speech to text..."):
        segments = transcribe_audio(audio_path)

    with st.spinner("🔍 Extracting conversation signals..."):
        st.session_state.results = detect_events(segments)

    if audio_path and os.path.exists(audio_path):
        os.remove(audio_path)

    st.success("✅ Analysis finished successfully!")

# -------------------------------------------------
# Display Results
# -------------------------------------------------
if st.session_state.results:
    tabs = st.tabs(["❓ Q&A Moments", "🤝 Agreements", "⚡ Conflicts"])

    def render_events(events, category):
        if not events:
            st.info("No insights detected in this category.")
            return

        video_id = get_video_id(st.session_state.current_video)

        for idx, e in enumerate(events):
            start_time, end_time = get_context_range(e["start"], buffer_seconds)

            st.markdown(f"""
            <div class="card">
                <div class="tag">⏰ {start_time} → {end_time}</div>
                <p>{e["text"]}</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"▶️ Watch Segment {idx+1}", key=f"play_{category}_{idx}"):
                start_sec = mmss_to_seconds(start_time)
                end_sec = mmss_to_seconds(end_time)

                # Play clip via iframe
                st.markdown(f"""
                    <iframe width="100%" height="315"
                        src="https://www.youtube.com/embed/{video_id}?start={start_sec}&end={end_sec}&autoplay=1"
                        frameborder="0" allow="autoplay; encrypted-media" allowfullscreen>
                    </iframe>
                """, unsafe_allow_html=True)

    with tabs[0]:
        render_events(st.session_state.results["qa"], "qa")
    with tabs[1]:
        render_events(st.session_state.results["agreement"], "agreement")
    with tabs[2]:
        render_events(st.session_state.results["disagreement"], "disagreement")

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.markdown("""
<div class="footer">
    Built with ❤️ using Streamlit & OpenAI Whisper<br>
    Academic / Research Use Only
</div>
""", unsafe_allow_html=True)
