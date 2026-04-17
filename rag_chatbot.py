"""
Lebanese Agricultural Guide RAG Chatbot
Author: Nizar Shehayeb
"""

import streamlit as st
import PyPDF2
import requests
import os
import json
import re
import base64
import tempfile
import asyncio
import numpy as np
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Optional: edge-tts provides free neural text-to-speech via Microsoft's API.
# Gracefully degrade if unavailable (e.g. restricted environments).
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# Optional: audio_recorder_streamlit enables browser mic input.
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

# Load .env for API keys (OPENROUTER_API_KEY, etc.). Not used in production
# on Streamlit Cloud where secrets are injected as env vars.
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PDF_PATH = "Agricultural Guide for Lebanon.pdf"  # Knowledge base PDF
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Rate-limiting thresholds to prevent API cost overruns
MAX_QUERIES_PER_SESSION = 25      # Per browser session (resets on page refresh)
MAX_QUERIES_PER_DAY_GLOBAL = 300  # Shared across all users (server-side counter)
COOLDOWN_SECONDS = 3              # Minimum seconds between consecutive queries

# Only cost-effective models are exposed to avoid burning credits
MODEL_OPTIONS = {
    "GPT-3.5 Turbo": "openai/gpt-3.5-turbo",
    "Claude 3 Haiku": "anthropic/claude-3-haiku-20240307",
    "Llama 3 70B": "meta-llama/llama-3-70b-instruct",
}

# Suggested prompts shown as clickable chips when the chat is empty.
# These guide first-time users and demonstrate the bot's capabilities.
SUGGESTED_PROMPTS = [
    "🫒 What olive varieties grow best in Lebanon?",
    "🍇 When should I harvest grapes in the Bekaa Valley?",
    "💧 What are the best irrigation methods for Lebanese farms?",
    "🌾 What crops are suitable for South Lebanon?",
    "🐛 How do I deal with citrus pests organically?",
    "🍎 What apple varieties are recommended for Mount Lebanon?",
]

# ---------------------------------------------------------------------------
# Page config & custom CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Lebanese Agriculture Guide",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* Global font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Hide default Streamlit branding */
#MainMenu, footer, header {visibility: hidden;}

/* Chat container */
.block-container { max-width: 860px; padding-top: 1.5rem; padding-bottom: 0; }

/* Source reference card */
.source-card {
    background: #f0fdf4;
    border-left: 4px solid #16a34a;
    padding: 0.75rem 1rem;
    margin: 0.25rem 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.85rem;
    line-height: 1.5;
    color: #1e293b;
}
.source-header {
    font-weight: 600;
    color: #15803d;
    margin-bottom: 0.3rem;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

/* Confidence badge */
.confidence-high { color: #16a34a; font-weight: 600; }
.confidence-med  { color: #ca8a04; font-weight: 600; }
.confidence-low  { color: #dc2626; font-weight: 600; }

/* Header */
.app-header {
    text-align: center;
    padding: 1rem 0 0.5rem;
}
.app-header h1 {
    font-size: 1.6rem;
    font-weight: 700;
    color: #15803d;
    margin: 0;
}
.app-header p {
    font-size: 0.9rem;
    color: #64748b;
    margin: 0.2rem 0 0;
}

/* Welcome card shown when chat is empty */
.welcome-card {
    background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 50%, #d1fae5 100%);
    border: 1px solid #bbf7d0;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin: 1.5rem auto;
    max-width: 640px;
    text-align: center;
}
.welcome-card h2 {
    font-size: 1.3rem;
    font-weight: 600;
    color: #15803d;
    margin: 0 0 0.5rem;
}
.welcome-card p {
    font-size: 0.88rem;
    color: #475569;
    margin: 0 0 0.3rem;
    line-height: 1.5;
}

/* Capability pills shown inside welcome card */
.capabilities {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    justify-content: center;
    margin-top: 1rem;
}
.capability-pill {
    background: white;
    border: 1px solid #d1fae5;
    border-radius: 20px;
    padding: 0.35rem 0.9rem;
    font-size: 0.78rem;
    color: #15803d;
    font-weight: 500;
}

/* Suggestion prompt chips — clickable quick-start questions */
.suggestion-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    justify-content: center;
    margin: 1rem auto 0.5rem;
    max-width: 700px;
}

/* Feedback (thumbs) inline on assistant messages */
.feedback-row {
    display: flex;
    gap: 0.4rem;
    margin-top: 0.4rem;
    align-items: center;
}
.feedback-row button {
    background: none;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 0.15rem 0.5rem;
    cursor: pointer;
    font-size: 0.82rem;
    color: #64748b;
    transition: all 0.15s;
}
.feedback-row button:hover {
    background: #f0fdf4;
    border-color: #16a34a;
    color: #16a34a;
}

/* Divider between welcome and suggestions */
.section-label {
    text-align: center;
    font-size: 0.75rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 1.2rem 0 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------
def detect_language(text):
    """Detect whether input text is primarily Arabic or English.
    Uses Unicode range counting — if >30% of characters are Arabic,
    the text is treated as Arabic for prompt/response language matching."""
    arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    total = arabic_chars + english_chars
    if total == 0:
        return "english"
    return "arabic" if arabic_chars / total > 0.3 else "english"


# ---------------------------------------------------------------------------
# PDF extraction with structure awareness
# ---------------------------------------------------------------------------
def extract_text_from_pdf(pdf_path):
    """Read every page of the PDF and return a list of {page, text} dicts.
    Skips pages with no extractable text (e.g. image-only pages)."""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"page": i + 1, "text": text})
    return pages


# ---------------------------------------------------------------------------
# Improved chunking — sentence-aware, with page numbers
# ---------------------------------------------------------------------------
def chunk_text_smart(pages, chunk_size=600, overlap=150):
    """Split text into overlapping chunks that respect sentence boundaries
    and track source page numbers."""
    chunks = []

    for page_info in pages:
        page_num = page_info["page"]
        text = page_info["text"]

        # Split into sentences (handles both Arabic and English)
        sentences = re.split(r'(?<=[.!?؟\n])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > chunk_size and current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "page": page_num,
                })
                # Keep overlap from end of previous chunk
                words = current_chunk.split()
                overlap_words = words[-max(1, len(words) // 3):]
                current_chunk = " ".join(overlap_words) + " " + sentence
            else:
                current_chunk = (current_chunk + " " + sentence).strip()

        # Don't forget the last chunk
        if current_chunk.strip() and len(current_chunk.strip()) >= 80:
            chunks.append({
                "text": current_chunk.strip(),
                "page": page_num,
            })

    return chunks


# ---------------------------------------------------------------------------
# Vectorizer with better text processing
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Indexing the Agricultural Guide…")
def _build_search_index(pdf_path):
    """Extract, chunk, and vectorize the PDF (cached across reruns)."""
    pages = extract_text_from_pdf(pdf_path)
    chunks = chunk_text_smart(pages)

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
        max_df=0.95,
        token_pattern=r"(?u)\b\w[\w']+\b",
    )
    texts = [c["text"] for c in chunks]
    vectors = vectorizer.fit_transform(texts)
    return chunks, vectorizer, vectors


def get_relevant_chunks(query, chunks, vectorizer, vectors, top_k=5):
    """Retrieve the top-k most relevant chunks for a query.
    Uses both the original query and an expanded version (singular/plural)
    to improve recall. De-duplicates near-identical passages."""
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, vectors).flatten()

    # Also try an expanded query
    expanded = _expand_query(query)
    if expanded != query:
        expanded_vec = vectorizer.transform([expanded])
        expanded_scores = cosine_similarity(expanded_vec, vectors).flatten()
        scores = np.maximum(scores, expanded_scores)

    ranked = scores.argsort()[::-1]

    results = []
    seen_texts = set()
    for idx in ranked:
        if scores[idx] < 0.02:
            break
        text_sig = chunks[idx]["text"][:100]
        if text_sig in seen_texts:
            continue
        seen_texts.add(text_sig)
        results.append({
            "text": chunks[idx]["text"],
            "page": chunks[idx]["page"],
            "score": float(scores[idx]),
        })
        if len(results) >= top_k:
            break

    return results


def _expand_query(query):
    """Simple query expansion — add singular/plural forms."""
    q = query.lower().strip()
    expansions = []
    for w in q.split():
        expansions.append(w)
        if w.endswith("s") and len(w) > 3:
            expansions.append(w[:-1])
        elif not w.endswith("s") and len(w) > 2:
            expansions.append(w + "s")
    return " ".join(expansions)


# ---------------------------------------------------------------------------
# LLM query with grounded prompt
# ---------------------------------------------------------------------------
def query_openrouter(query, context_chunks, model, temperature=0.4, max_tokens=600):
    """Send the query + retrieved context to an LLM via OpenRouter.
    Uses a two-tier prompt strategy:
      1. Answer from guide sources with [Source N] citations
      2. If guide is insufficient, supplement with general agricultural knowledge
         clearly labeled so the user can distinguish verified vs. general info.
    Returns (answer_text, context_chunks) tuple."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "Error: OpenRouter API key not configured.", []

    lang = detect_language(query)
    has_sources = bool(context_chunks)

    # Build numbered context block (may be empty if no chunks matched)
    context_parts = []
    for i, c in enumerate(context_chunks, 1):
        context_parts.append(f"[Source {i} — Page {c['page']}]\n{c['text']}")
    context_text = "\n\n".join(context_parts) if context_parts else "(No relevant passages found in the guide.)"

    # --- Two-tier prompt: guide-first, then general knowledge if needed ---
    if lang == "arabic":
        system_msg = """أنت مساعد زراعي متخصص في الزراعة اللبنانية.

القواعد:
1. أولاً، أجب باستخدام المصادر المقدمة أدناه. أشر إلى رقم المصدر عند الاستشهاد (مثال: [المصدر 1]).
2. إذا كانت المصادر لا تغطي الموضوع بالكامل أو لا تحتوي على معلومات كافية، اذكر ذلك بوضوح ثم قدّم معلومات إضافية مفيدة من معرفتك الزراعية العامة.
3. ميّز بوضوح بين المعلومات من الدليل (مع الاستشهاد) والمعلومات من المعرفة العامة باستخدام عنوان "📚 معلومات عامة:" للقسم غير المستند إلى الدليل.
4. كن عملياً ومحدداً.
5. أجب باللغة العربية."""
    else:
        system_msg = """You are an agricultural advisor specializing in Lebanese farming.

Rules:
1. First, answer using the provided source passages below. Cite sources with [Source N] when referencing guide content.
2. If the sources do not fully cover the topic or lack sufficient detail, clearly state what the guide does not cover, then provide additional helpful information from your general agricultural knowledge.
3. Clearly separate guide-sourced information (with citations) from general knowledge. Use the heading "📚 General Knowledge:" before any information not from the guide.
4. Be specific and practical — give actionable advice.
5. Never refuse to answer. Always be helpful."""

    user_msg = f"""Sources from the Lebanese Agricultural Guide:

{context_text}

Question: {query}"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://farmerschatbot.com",
        "X-Title": "Lebanese Agricultural Guide Chatbot",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"], context_chunks
            except (KeyError, IndexError, TypeError):
                return "Error: Unexpected API response format.", context_chunks
        else:
            return f"Error: API returned status {resp.status_code}.", context_chunks
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again.", context_chunks
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to the API. Check your internet.", context_chunks
    except Exception as e:
        return f"Error: {str(e)}", context_chunks


def fallback_answer(query, context_chunks):
    """Basic keyword-matching answer when API is unavailable."""
    lang = detect_language(query)
    keywords = query.lower().split()
    hits = []
    for c in context_chunks:
        matching = sum(1 for k in keywords if k in c["text"].lower())
        if matching > 0:
            hits.append((matching, c))
    hits.sort(key=lambda x: -x[0])
    if hits:
        texts = [f"**Page {c['page']}:** {c['text'][:300]}…" for _, c in hits[:3]]
        prefix = "إليك أقرب النتائج من الدليل:" if lang == "arabic" else "Here are the closest matches from the guide:"
        return prefix + "\n\n" + "\n\n".join(texts)
    return "لم يتم العثور على نتائج مطابقة." if lang == "arabic" else "No matching results found in the guide."


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
def check_rate_limit():
    """Three-layer rate limiter:
    1. Per-session cap (resets on page refresh)
    2. Global daily cap (shared counter in temp file)
    3. Cooldown between consecutive queries
    Returns (allowed: bool, error_message: str | None)."""
    import time
    from datetime import date

    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
    if "last_query_time" not in st.session_state:
        st.session_state.last_query_time = 0

    today = date.today().isoformat()
    counter_file = os.path.join(tempfile.gettempdir(), "openrouter_daily_count.json")

    try:
        if os.path.exists(counter_file):
            with open(counter_file, "r") as f:
                daily_data = json.load(f)
            if daily_data.get("date") != today:
                daily_data = {"date": today, "count": 0}
        else:
            daily_data = {"date": today, "count": 0}
    except Exception:
        daily_data = {"date": today, "count": 0}

    if st.session_state.query_count >= MAX_QUERIES_PER_SESSION:
        return False, f"Session limit reached ({MAX_QUERIES_PER_SESSION}). Refresh the page to start a new session."
    if daily_data["count"] >= MAX_QUERIES_PER_DAY_GLOBAL:
        return False, "Daily limit reached. Please try again tomorrow."
    elapsed = time.time() - st.session_state.last_query_time
    if elapsed < COOLDOWN_SECONDS:
        return False, f"Please wait {int(COOLDOWN_SECONDS - elapsed) + 1}s between queries."

    st.session_state.query_count += 1
    st.session_state.last_query_time = time.time()
    daily_data["count"] += 1
    try:
        with open(counter_file, "w") as f:
            json.dump(daily_data, f)
    except Exception:
        pass
    return True, None


# ---------------------------------------------------------------------------
# Edge TTS
# ---------------------------------------------------------------------------
def text_to_speech_edge(text, language="english"):
    """Generate speech audio from text using Microsoft's free edge-tts.
    Returns (audio_bytes, error_string). One of them will be None."""
    if not EDGE_TTS_AVAILABLE:
        return None, "edge-tts not available"
    try:
        voice = "ar-SA-HamedNeural" if language == "arabic" else "en-US-JennyNeural"

        async def _gen():
            comm = edge_tts.Communicate(text, voice)
            fd, path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            await comm.save(path)
            return path

        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        path = loop.run_until_complete(_gen())
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, "rb") as f:
                data = f.read()
            try:
                os.unlink(path)
            except Exception:
                pass
            return data, None
        return None, "TTS produced empty output"
    except Exception as e:
        return None, f"TTS error: {str(e)}"


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------
def render_sources(context_chunks):
    """Show the retrieved source chunks for transparency."""
    if not context_chunks:
        return
    with st.expander("📄 View source passages from the guide", expanded=False):
        for i, c in enumerate(context_chunks, 1):
            score_pct = int(c["score"] * 100)
            if score_pct >= 30:
                badge = f'<span class="confidence-high">● {score_pct}% match</span>'
            elif score_pct >= 15:
                badge = f'<span class="confidence-med">● {score_pct}% match</span>'
            else:
                badge = f'<span class="confidence-low">● {score_pct}% match</span>'
            st.markdown(
                f'<div class="source-card">'
                f'<div class="source-header">Source {i} — Page {c["page"]}  {badge}</div>'
                f'{c["text"][:400]}{"…" if len(c["text"]) > 400 else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_audio_button(text, lang, key):
    """Render a TTS play button."""
    if not EDGE_TTS_AVAILABLE:
        return
    if st.button("🔊 Listen", key=key):
        with st.spinner("Generating audio…"):
            audio, err = text_to_speech_edge(text, lang)
            if err:
                st.warning(f"Could not generate audio: {err}")
            elif audio:
                b64 = base64.b64encode(audio).decode()
                st.markdown(
                    f'<audio controls autoplay><source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg"></audio>',
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    # --- Header ---
    st.markdown(
        '<div class="app-header">'
        '<h1>🌿 Lebanese Agricultural Guide</h1>'
        '<p>AI-powered assistant — answers grounded in the official Agricultural Guide for Lebanon</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # --- Load data ---
    if not os.path.exists(PDF_PATH):
        st.error(f"'{PDF_PATH}' not found in the project directory.")
        return

    chunks, vectorizer, vectors = _build_search_index(PDF_PATH)

    # --- Sidebar: settings, session controls, and info ---
    with st.sidebar:
        st.markdown("### ⚙️ Settings")

        selected_model_name = st.selectbox("AI Model", list(MODEL_OPTIONS.keys()), index=0)
        selected_model = MODEL_OPTIONS[selected_model_name]

        temperature = st.slider("Creativity", 0.0, 1.0, 0.3, 0.1,
                                help="Lower = more factual, higher = more creative")
        max_tokens = st.slider("Max response length", 200, 800, 500, 50)

        st.markdown("---")

        # New Chat button — clears conversation history so the user can start fresh
        if st.button("🗑️ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        if "query_count" not in st.session_state:
            st.session_state.query_count = 0
        remaining = MAX_QUERIES_PER_SESSION - st.session_state.query_count
        st.metric("Queries remaining", f"{remaining}")

        st.markdown("---")
        st.caption(f"📚 {len(chunks)} passages indexed")
        if EDGE_TTS_AVAILABLE:
            st.caption("🔊 Voice output available")
        else:
            st.caption("🔇 Voice output unavailable (edge-tts)")

        # About section — brief explainer for new users
        st.markdown("---")
        with st.expander("ℹ️ About this app"):
            st.markdown(
                "This chatbot answers questions about Lebanese agriculture "
                "using the official *Agricultural Guide for Lebanon* as its "
                "primary knowledge source. Answers include source citations so "
                "you can verify guide-based claims.\n\n"
                "When the guide doesn’t fully cover a topic, the assistant "
                "supplements with general agricultural knowledge, clearly "
                "labeled as “General Knowledge” so you always know what’s "
                "from the guide vs. the AI.\n\n"
                "Built with ❤️ by Nizar Shehayeb"
            )

    # --- Chat history ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- Welcome screen (shown only when chat is empty) ---
    if not st.session_state.messages:
        st.markdown(
            '<div class="welcome-card">'
            '<h2>🌱 Welcome! أهلاً وسهلاً!</h2>'
            '<p>I\'m your AI farming assistant for Lebanon. Ask me anything about crops, '
            'irrigation, pest control, soil management, and more. I\'ll check the official '
            'Agricultural Guide first, and supplement with expert knowledge when needed.</p>'
            '<div class="capabilities">'
            '<span class="capability-pill">🌿 Crop recommendations</span>'
            '<span class="capability-pill">💧 Irrigation advice</span>'
            '<span class="capability-pill">🐛 Pest management</span>'
            '<span class="capability-pill">🌍 Regional guidance</span>'
            '<span class="capability-pill">📅 Seasonal planning</span>'
            '<span class="capability-pill">🍊 Fruit & vegetable care</span>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Suggestion chips — clickable starter questions for first-time users
        st.markdown('<p class="section-label">Try one of these questions</p>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, prompt in enumerate(SUGGESTED_PROMPTS):
            with cols[i % 3]:
                if st.button(prompt, key=f"suggest_{i}", use_container_width=True):
                    # Inject the suggested prompt as if the user typed it
                    st.session_state.pending_prompt = prompt
                    st.rerun()

    # Render previous messages (with sources and audio on assistant turns)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🌿" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                render_sources(msg["sources"])

    # --- Chat input ---
    # Check if a suggested prompt was clicked (set during rerun)
    user_input = st.chat_input("Ask about Lebanese agriculture…  /  اسأل عن الزراعة اللبنانية")
    if "pending_prompt" in st.session_state:
        user_input = st.session_state.pop("pending_prompt")

    if user_input:
        # Append user message to history and render it immediately
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Rate-limit check: session cap, daily cap, and cooldown
        allowed, limit_msg = check_rate_limit()
        if not allowed:
            with st.chat_message("assistant", avatar="🌿"):
                st.warning(f"⏳ {limit_msg}")
            return

        lang = detect_language(user_input)

        # --- Retrieve relevant passages & generate a grounded answer ---
        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner("Searching the guide & generating answer…" if lang == "english"
                            else "جارٍ البحث وإنشاء الإجابة…"):
                context_chunks = get_relevant_chunks(user_input, chunks, vectorizer, vectors, top_k=5)

                # Always call the LLM — even with no/few chunks.
                # The two-tier prompt will use guide sources when available
                # and supplement with general knowledge when needed.
                answer, sources = query_openrouter(
                    user_input, context_chunks, selected_model, temperature, max_tokens
                )

                # If the API call failed, fall back to simple keyword matching
                if answer.startswith("Error:"):
                    st.warning(answer)
                    answer = fallback_answer(user_input, context_chunks)

                st.markdown(answer)
                # Only show source panel if retrieval found relevant passages
                if sources:
                    render_sources(sources)
                render_audio_button(answer, lang, key=f"tts_{len(st.session_state.messages)}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
            })


if __name__ == "__main__":
    main()
