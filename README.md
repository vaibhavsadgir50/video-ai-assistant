# 🎬 Video AI Assistant

Turn any video — a YouTube link or a file from your device — into a title, a summary,
action items, key decisions, open questions, and a chatbot that answers questions about
the video using only what was actually said in it.

**🌐 Multi Language support Assistant** Give it an English video or any other one —
transcription, summary, and chat all work either way.

**RAG for Questions related to video** Ask any question about the video, it can answer and explain you well with follow ups

---

## ✨ Features

- **Paste a YouTube link or upload a file** — video or audio, local file or URL.
- **Auto-generated title & summary** of the whole video.
- **Action items, key decisions & open questions** extracted automatically.
- **Chat with your video** — ask follow-up questions and get answers grounded in the
  transcript, not the model's imagination. Thanks to RAG implementation.
- **Multi-language support** — multi audio are both handled out of
  the box.
- **Clean Streamlit UI** — a single-page app: landing → upload → processing → results,
  with a theatre-mode video player and a WhatsApp-style chat panel.

---

## 🧠 How it works

```
Video / YouTube URL
        │
        ▼
 ┌────────────────┐   yt-dlp + pydub
 │ Audio pipeline  │   download → convert to mono 16kHz WAV → chunk into 10-min pieces
 └────────────────┘
        │
        ▼
 ┌────────────────┐   OpenAI Whisper (local)  — English
 │ Transcription   │   Sarvam AI STT-translate — Hindi / Hinglish → English text
 └────────────────┘
        │
        ▼
 ┌────────────────┐   LangChain + an LLM (via OpenRouter)
 │ Summarize /     │   title, summary, action items, decisions, open questions
 │ Extract         │
 └────────────────┘
        │
        ▼
 ┌────────────────┐   Chroma + sentence-transformer embeddings
 │ RAG chat        │   transcript → chunks → embeddings → vector store → retriever
 └────────────────┘   question → similarity search → top-k chunks → LLM answer
```

### Why RAG?

Feeding an entire transcript into a chat prompt on every question is slow, expensive,
and runs into context-window limits on long videos. Instead, this project uses
**Retrieval-Augmented Generation (RAG)**:

1. The transcript is split into overlapping chunks (`core/vector_store.py`).
2. Each chunk is embedded into a vector using a local HuggingFace sentence-transformer
   model (`all-MiniLM-L6-v2` — no API call, runs on CPU).
3. The embeddings are stored in a local **Chroma** vector database.
4. When you ask a question, the question itself is embedded and compared against the
   stored chunks to retrieve the most relevant ones (`get_retriver`, k=4 by default).
5. Only those few relevant chunks — not the whole transcript — are passed to the LLM
   along with your question, through a LangChain **LCEL** chain
   (`core/rag_engine.py`), so the answer stays grounded in what the video actually said.

Each new video rebuilds the vector store from scratch, so answers never mix content
from a previously analyzed video.

---

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io) (`app.py`) |
| Video/audio ingestion | [`yt-dlp`](https://github.com/yt-dlp/yt-dlp), [`pydub`](https://github.com/jiaaro/pydub), FFmpeg |
| Speech-to-text (English) | [OpenAI Whisper](https://github.com/openai/whisper) — runs **locally**, no API key needed |
| Speech-to-text (Hindi / Hinglish) | [Sarvam AI](https://sarvam.ai) speech-to-text-translate API |
| LLM orchestration | [LangChain](https://www.langchain.com) (LCEL chains, prompt templates, output parsers) |
| LLM inference | [OpenRouter](https://openrouter.ai) (model-agnostic LLM gateway) |
| Embeddings | HuggingFace `sentence-transformers` (`all-MiniLM-L6-v2`), local & free |
| Vector store / RAG | [Chroma](https://www.trychroma.com) |
| Config | `python-dotenv` |

---

## 📦 Requirements

- Python 3.10+ (project tested with 3.12/3.14)
- [FFmpeg](https://ffmpeg.org) installed and on your `PATH` (`brew install ffmpeg` on macOS)
- An [OpenRouter](https://openrouter.ai/keys) API key (for summaries, extraction and chat)
- A [Sarvam AI](https://dashboard.sarvam.ai) API key **only if** you want Hindi/Hinglish
  support — English-only transcription runs fully locally with Whisper and needs no
  speech-to-text API key at all

---

## 🚀 Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/<your-username>/video-ai-assistant.git
   cd video-ai-assistant
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r Requirements.txt
   ```

4. **Install FFmpeg** (required by `pydub`/`yt-dlp`)
   ```bash
   brew install ffmpeg            # macOS
   # or: sudo apt install ffmpeg  # Debian/Ubuntu
   ```

5. **Set up your API keys**
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and fill in:

   | Variable | Required? | What it's for |
   |---|---|---|
   | `OPENROUTER_API_KEY` | ✅ Yes | Powers the LLM calls — summary, title, extraction, and RAG chat answers |
   | `SARVAM_API_KEY` | Only for Hindi/Hinglish videos | Speech-to-text for Hindi/Hinglish audio |
   | `SARVAM_STT_MODEL` | Optional | Defaults to `saaras:v2.5` |
   | `WHISPER_MODEL` | Optional | Local Whisper model size for English audio: `tiny`/`base`/`small`/`medium`/`large` (default `small`) |
   | `MISTRAL_API_KEY` | Optional | Only needed if you switch the LLM provider to Mistral directly |

   English transcription uses Whisper **locally** on your machine — no key needed for
   that part. Only the LLM step (summaries/chat) requires `OPENROUTER_API_KEY`.

6. **Run the app**
   ```bash
   streamlit run app.py
   ```
   Open the URL Streamlit prints (usually `http://localhost:8501`).

---

## ▶️ Usage

1. Open the app and click **Try Now**.
2. Paste a YouTube URL *or* upload a video/audio file, and pick the language
   (English or Hinglish).
3. Click **Submit** and wait while the app downloads/converts the audio, transcribes
   it, and generates the summary.
4. On the results page you'll see:
   - The video, in a centered theatre-mode player.
   - A panel with the generated **title, summary, action items, decisions and open
     questions**.
   - A **chat panel** where you can ask follow-up questions about the video.

You can also run the pipeline from the command line:
```bash
python main.py
```

---

## 📁 Project structure

```
app.py                  # Streamlit UI (single file)
main.py                 # Pipeline orchestration (CLI entry point)
core/
  transcriber.py         # Whisper (English) + Sarvam AI (Hindi/Hinglish) STT
  summarize.py            # Title & summary generation (LangChain + OpenRouter)
  extractor.py             # Action items / decisions / open questions extraction
  vector_store.py           # Chunking, embeddings, Chroma vector store
  rag_engine.py               # RAG retrieval + chat chain
utils/
  audio_processor.py      # yt-dlp download, format conversion, chunking
```

---

## ⚠️ Notes

- `downloads/` and `vector_db/` are created at runtime and are git-ignored — don't
  commit them.
- Never commit your real `.env` file; only `.env.example` is tracked.
- Free-tier LLM models on OpenRouter are rate-limited and can occasionally return
  `429`/provider-unavailable errors. If that happens, try again shortly or switch the
  model in `core/summarize.py`, `core/extractor.py`, and `core/rag_engine.py`.
