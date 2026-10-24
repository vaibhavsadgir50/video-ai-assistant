import os
import re
import time
import tempfile

import streamlit as st

from main import run_pipeline
from core.rag_engine import ask_question

st.set_page_config(page_title="Video AI Assistant", page_icon="🎬", layout="wide")

# ──────────────────────────────────────────────────────────────────────────
# Global style — light glass theme
# ──────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #eef3fb 0%, #e7eefc 30%, #f3ecfb 65%, #eef7f4 100%);
        background-attachment: fixed;
        color: #1b2430;
    }
    [data-testid="stAppViewContainer"] > .main {
        background: transparent;
    }
    .block-container {
        padding-top: 2.2rem;
        max-width: 1100px;
    }

    .glass {
        background: rgba(255, 255, 255, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.65);
        border-radius: 26px;
        box-shadow: 0 8px 32px rgba(60, 80, 130, 0.14), inset 0 1px 0 rgba(255,255,255,0.6);
        backdrop-filter: blur(18px) saturate(160%);
        -webkit-backdrop-filter: blur(18px) saturate(160%);
        padding: 2.2rem 2.4rem;
        margin-bottom: 1.6rem;
    }
    .glass-tight { padding: 1.4rem 1.6rem; }

    .hero-title {
        font-size: 3.1rem;
        font-weight: 800;
        text-align: center;
        letter-spacing: 0.5px;
        background: linear-gradient(90deg, #4b6fff, #8a5bff, #4b6fff);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-sub {
        text-align: center;
        font-size: 1.15rem;
        color: #4a5568;
        margin-bottom: 1.6rem;
    }
    .flow-step {
        text-align: center;
        padding: 1.2rem 0.8rem;
    }
    .flow-emoji { font-size: 2.1rem; }
    .flow-label { font-weight: 700; margin-top: 0.4rem; color: #2d3a4f; }
    .flow-desc { font-size: 0.92rem; color: #5a6578; margin-top: 0.2rem; }
    .flow-arrow { text-align: center; font-size: 1.8rem; color: #9aa6c3; padding-top: 1.6rem; }

    div.stButton > button {
        background: linear-gradient(90deg, #5c7cfa, #9775fa);
        color: white;
        border: none;
        border-radius: 999px;
        padding: 0.7rem 2.2rem;
        font-weight: 700;
        font-size: 1.02rem;
        box-shadow: 0 6px 18px rgba(99, 102, 241, 0.35);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(99, 102, 241, 0.45);
    }

    .section-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: #2d3a4f;
        margin-bottom: 0.6rem;
    }

    .chat-row { display: flex; margin-bottom: 0.7rem; }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.bot { justify-content: flex-start; }
    .bubble {
        max-width: 72%;
        padding: 0.65rem 1rem;
        border-radius: 16px;
        font-size: 0.95rem;
        line-height: 1.45;
        box-shadow: 0 2px 10px rgba(60,80,130,0.10);
    }
    .bubble.user {
        background: linear-gradient(135deg, #d6e4ff, #c9f0dc);
        border: 1px solid rgba(255,255,255,0.7);
        border-bottom-right-radius: 4px;
        color: #1b2430;
    }
    .bubble.bot {
        background: rgba(255,255,255,0.75);
        border: 1px solid rgba(255,255,255,0.7);
        border-bottom-left-radius: 4px;
        color: #1b2430;
    }

    .stage-line {
        font-size: 1.05rem;
        color: #3c4a63;
        margin: 0.3rem 0;
    }
    .stage-done { color: #2f9e62; font-weight: 600; }
    .stage-active { color: #4b6fff; font-weight: 700; }
    .stage-pending { color: #a3acc2; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "hero"
if "result" not in st.session_state:
    st.session_state.result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of (question, answer)
if "video_source" not in st.session_state:
    st.session_state.video_source = None
if "video_kind" not in st.session_state:
    st.session_state.video_kind = None  # "youtube" | "file"


def goto(page: str):
    st.session_state.page = page


def is_youtube_url(text: str) -> bool:
    return bool(re.search(r"(youtube\.com|youtu\.be)", text or ""))


def youtube_id(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


# ──────────────────────────────────────────────────────────────────────────
# PAGE 1 — Hero
# ──────────────────────────────────────────────────────────────────────────
def render_hero():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">🎬 VIDEO AI ASSISTANT</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Turn any video into a title, summary, action items '
        'and a chat partner — just drop a link or a file.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns([1, 0.3, 1, 0.3, 1])
    with c1:
        st.markdown(
            '<div class="flow-step"><div class="flow-emoji">⬆️</div>'
            '<div class="flow-label">1. Upload</div>'
            '<div class="flow-desc">Paste a YouTube link or upload a video/audio file from your device.</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown('<div class="flow-arrow">→</div>', unsafe_allow_html=True)
    with c3:
        st.markdown(
            '<div class="flow-step"><div class="flow-emoji">📝</div>'
            '<div class="flow-label">2. Get Summary</div>'
            '<div class="flow-desc">We transcribe the audio and generate a title, summary, '
            "action items, decisions and open questions.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown('<div class="flow-arrow">→</div>', unsafe_allow_html=True)
    with c5:
        st.markdown(
            '<div class="flow-step"><div class="flow-emoji">💬</div>'
            '<div class="flow-label">3. Ask Questions</div>'
            '<div class="flow-desc">Chat with your video — ask anything, grounded in the real transcript.</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        if st.button("Try Now →", use_container_width=True):
            goto("upload")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────
# PAGE 2 — Upload
# ──────────────────────────────────────────────────────────────────────────
def render_upload():
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Add your video</div>', unsafe_allow_html=True)

        youtube_url = st.text_input("YouTube link", placeholder="https://www.youtube.com/watch?v=...")
        st.markdown("<div style='text-align:center;color:#9aa6c3;margin:0.4rem 0;'>— or —</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload from your device", type=["mp4", "mov", "mkv", "mp3", "wav", "m4a"])
        language = st.selectbox("Language", ["english", "hinglish"], index=0)

        submitted = st.button("Submit", use_container_width=True)

        if submitted:
            if youtube_url.strip():
                st.session_state.video_source = youtube_url.strip()
                st.session_state.video_kind = "youtube"
                st.session_state.language = language
                goto("processing")
                st.rerun()
            elif uploaded_file is not None:
                suffix = os.path.splitext(uploaded_file.name)[1] or ".mp4"
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                tmp.write(uploaded_file.read())
                tmp.close()
                st.session_state.video_source = tmp.name
                st.session_state.video_kind = "file"
                st.session_state.video_display_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else None
                st.session_state.language = language
                goto("processing")
                st.rerun()
            else:
                st.warning("Please paste a YouTube link or upload a file first.")

        st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────
# PAGE 3 — Processing
# ──────────────────────────────────────────────────────────────────────────
def render_processing():
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Working on your video…</div>', unsafe_allow_html=True)

        status_box = st.empty()
        stages = [
            "Downloading / preparing audio",
            "Transcribing speech to text",
            "Generating title & summary",
            "Extracting action items & decisions",
            "Building chat knowledge base",
        ]

        def render_stages(active_idx):
            lines = []
            for i, s in enumerate(stages):
                if i < active_idx:
                    lines.append(f'<div class="stage-line stage-done">✅ {s}</div>')
                elif i == active_idx:
                    lines.append(f'<div class="stage-line stage-active">⏳ {s}...</div>')
                else:
                    lines.append(f'<div class="stage-line stage-pending">⬜ {s}</div>')
            status_box.markdown("".join(lines), unsafe_allow_html=True)

        render_stages(0)
        try:
            result = run_pipeline(st.session_state.video_source, st.session_state.get("language", "english"))
            render_stages(len(stages))
            st.session_state.result = result
            time.sleep(0.4)
            goto("results")
            st.rerun()
        except Exception as e:
            st.error(f"Something went wrong while processing: {e}")
            if st.button("← Back"):
                goto("upload")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────
# PAGE 4 — Results
# ──────────────────────────────────────────────────────────────────────────
def render_video_player():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    if st.session_state.video_kind == "youtube":
        vid = youtube_id(st.session_state.video_source)
        if vid:
            st.markdown(
                f"""
                <div style="position:relative;width:100%;max-width:960px;margin:0 auto;
                            padding-top:56.25%;border-radius:18px;overflow:hidden;
                            box-shadow:0 10px 30px rgba(0,0,0,0.25);">
                  <iframe src="https://www.youtube.com/embed/{vid}"
                          style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
                          allowfullscreen></iframe>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.video(st.session_state.video_source)
    else:
        data = st.session_state.get("video_display_bytes")
        if data:
            st.video(data)
        else:
            st.video(st.session_state.video_source)
    st.markdown("</div>", unsafe_allow_html=True)


def render_summary_panel(result):
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">📌 {result.get("title", "Untitled")}</div>', unsafe_allow_html=True)
    st.markdown("**Summary**")
    st.write(result.get("summary", ""))

    analysis = result.get("analysis")
    st.markdown("**Analysis**")
    if isinstance(analysis, tuple):
        labels = ["Action Items", "Key Decisions", "Open Questions"]
        for label, content in zip(labels, analysis):
            with st.expander(label):
                for item in content:
                    st.write(item)
    else:
        st.write(analysis)
    st.markdown("</div>", unsafe_allow_html=True)


def render_chat_panel():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💬 Ask about this video</div>', unsafe_allow_html=True)

    for q, a in st.session_state.chat_history:
        st.markdown(f'<div class="chat-row user"><div class="bubble user">{q}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-row bot"><div class="bubble bot">{a}</div></div>', unsafe_allow_html=True)

    question = st.chat_input("Type your question...")
    if question:
        rag_chain = st.session_state.result["rag_chain"]
        answer = ask_question(rag_chain, question)
        st.session_state.chat_history.append((question, answer))
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_results():
    result = st.session_state.result
    render_video_player()
    col1, col2 = st.columns(2)
    with col1:
        render_summary_panel(result)
    with col2:
        render_chat_panel()


# ──────────────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────────────
page = st.session_state.page
if page == "hero":
    render_hero()
elif page == "upload":
    render_upload()
elif page == "processing":
    render_processing()
elif page == "results":
    render_results()
