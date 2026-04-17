"""
Lebanese Agricultural Guide RAG Chatbot with Voice Capabilities

A Retrieval-Augmented Generation (RAG) chatbot that provides expert agricultural advice
for Lebanese farming practices by combining document retrieval with AI-powered responses.
Enhanced with advanced voice input/output capabilities for natural interaction.

The system extracts knowledge from a PDF agricultural guide, chunks the content,
creates vector embeddings for semantic search, and uses retrieved context to generate
comprehensive answers through various Large Language Models. Features include real-time
speech-to-text input and human-like text-to-speech output in both Arabic and English.

Technologies Used:
- Streamlit: Web interface and user interaction
- PyPDF2: PDF document text extraction
- Scikit-learn: TF-IDF vectorization and cosine similarity for document retrieval
- OpenRouter API: Access to multiple LLMs (GPT-3.5/4, Claude, Llama, Mistral)
- ElevenLabs API: High-quality text-to-speech with human-like voices
- OpenAI Whisper API: Advanced speech-to-text transcription
- audio_recorder_streamlit: Real-time audio recording in browser
- Python-dotenv: Environment variable management
- Requests: HTTP API communication

RAG Pipeline:
1. Document Ingestion: Extract text from PDF and split into overlapping chunks
2. Vectorization: Create TF-IDF embeddings for semantic search
3. Retrieval: Find most relevant document chunks based on user query
4. Generation: Send retrieved context + query to LLM for comprehensive answers
5. Voice Processing: Convert between speech and text for natural interaction
6. Fallback: Provide basic text matching when API is unavailable

Voice Features:
- Speech-to-Text: Record questions directly in browser using OpenAI Whisper
- Text-to-Speech: Convert responses to natural speech using ElevenLabs
- Language Detection: Automatically detect Arabic vs English for appropriate voice selection
- Bilingual Interface: Complete Arabic/English support throughout the application

Author: Nizar Shehayeb
"""

import streamlit as st
import PyPDF2
import requests
import os
import json
import re
import io
import base64
import tempfile
# Import torch modules first to avoid circular imports
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
import numpy as np
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from audio_recorder_streamlit import audio_recorder

# Local TTS and STT imports
try:
    # Import TTS after torch to avoid circular import issues
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError as e:
    TTS_AVAILABLE = False
    TTS_IMPORT_ERROR = str(e)
    
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError as e:
    WHISPER_AVAILABLE = False
    WHISPER_IMPORT_ERROR = str(e)

try:
    from pyht import Client
    from pyht.client import TTSOptions
    PLAYHT_AVAILABLE = True
except ImportError as e:
    PLAYHT_AVAILABLE = False
    PLAYHT_IMPORT_ERROR = str(e)

# Load environment variables
load_dotenv()

# Global variables
PDF_PATH = 'Agricultural Guide for Lebanon.pdf'
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
DOCUMENT_TEXT = ""
CHUNKS = []
VECTORIZER = None
VECTORS = None

# Rate limiting settings
MAX_QUERIES_PER_SESSION = 20      # Per user session
MAX_QUERIES_PER_DAY_GLOBAL = 200  # Across all users combined
COOLDOWN_SECONDS = 5              # Minimum seconds between queries

# Local model variables
TTS_MODEL = None
WHISPER_MODEL = None
PLAYHT_CLIENT = None

def detect_language(text):
    """Simple language detection for Arabic vs English"""
    # Count Arabic characters (Unicode range for Arabic script)
    arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
    # Count English characters
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    # If more than 30% of characters are Arabic, consider it Arabic
    total_chars = arabic_chars + english_chars
    if total_chars == 0:
        return "english"  # Default to English if no detectable characters
    
    arabic_ratio = arabic_chars / total_chars
    return "arabic" if arabic_ratio > 0.3 else "english"

@st.cache_resource(show_spinner=False)
def _load_playht_client():
    """Load PlayHT client (cached across reruns)"""
    if not PLAYHT_AVAILABLE:
        return None
    try:
        user_id = os.getenv("PLAYHT_USER_ID")
        api_key = os.getenv("PLAYHT_API_KEY")
        if user_id and api_key:
            return Client(user_id=user_id, api_key=api_key)
    except Exception:
        pass
    return None

@st.cache_resource(show_spinner=False)
def _load_tts_model():
    """Load local TTS model (cached across reruns)"""
    if not TTS_AVAILABLE or not TORCH_AVAILABLE:
        return None
    try:
        models_to_try = [
            "tts_models/en/ljspeech/tacotron2-DDC",
            "tts_models/en/ljspeech/glow-tts",
            "tts_models/en/ljspeech/speedy-speech"
        ]
        for model_name in models_to_try:
            try:
                return TTS(model_name, gpu=torch.cuda.is_available())
            except Exception:
                continue
    except Exception:
        pass
    return None

@st.cache_resource(show_spinner=False)
def _load_whisper_model():
    """Load Whisper STT model (cached across reruns)"""
    if not WHISPER_AVAILABLE or not TORCH_AVAILABLE:
        return None
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return whisper.load_model("base", device=device)
    except Exception:
        pass
    return None

@st.cache_resource(show_spinner="Loading the Agricultural Guide...")
def _load_and_process_pdf(pdf_path):
    """Load PDF and create search index (cached across reruns)"""
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    vectorizer, vectors = create_vectorizer(chunks)
    return text, chunks, vectorizer, vectors

def load_local_models():
    """Load local TTS and STT models using cached loaders"""
    global TTS_MODEL, WHISPER_MODEL, PLAYHT_CLIENT
    PLAYHT_CLIENT = _load_playht_client()
    TTS_MODEL = _load_tts_model()
    WHISPER_MODEL = _load_whisper_model()

def text_to_speech_local(text, language="english"):
    """Convert text to speech using local TTS model"""
    global TTS_MODEL
    
    if not TTS_AVAILABLE or TTS_MODEL is None:
        return None, "Local TTS model not available. Please install TTS: pip install TTS"
    
    try:
        # Create a temporary file for output with proper Windows handling
        import tempfile
        import os
        
        # Create temporary directory if it doesn't exist
        temp_dir = tempfile.gettempdir()
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # Create a temporary file for output
        fd, output_path = tempfile.mkstemp(suffix=".wav", dir=temp_dir)
        os.close(fd)  # Close the file descriptor immediately
        
        # Generate speech using the simpler model
        TTS_MODEL.tts_to_file(
            text=text,
            file_path=output_path
        )
        
        # Read the generated audio file
        if os.path.exists(output_path):
            with open(output_path, "rb") as audio_file:
                audio_content = audio_file.read()
            
            # Clean up temporary file
            try:
                os.unlink(output_path)
            except:
                pass  # Ignore cleanup errors
            
            return audio_content, None
        else:
            return None, "Failed to generate audio file"
        
    except Exception as e:
        return None, f"Error generating speech: {str(e)}"

def speech_to_text_local(audio_bytes):
    """Convert speech to text using local Whisper model with improved Arabic/English support"""
    global WHISPER_MODEL
    
    if not WHISPER_AVAILABLE or WHISPER_MODEL is None:
        return None, "Local STT model not available. Please install openai-whisper: pip install openai-whisper"
    
    try:
        import tempfile
        import os
        
        # Validate input
        if not audio_bytes or len(audio_bytes) == 0:
            return None, "No audio data received"
        
        # Create temporary directory if it doesn't exist
        temp_dir = tempfile.gettempdir()
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # Save audio bytes to temporary file with proper Windows handling
        fd, audio_path = tempfile.mkstemp(suffix=".wav", dir=temp_dir)
        
        try:
            # Write audio data to the file
            with os.fdopen(fd, 'wb') as tmp_file:
                tmp_file.write(audio_bytes)
            
            # Verify file exists and has content
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                return None, "Failed to create temporary audio file"
            
            # Transcribe using Whisper with enhanced options for Arabic/English
            result = WHISPER_MODEL.transcribe(
                audio_path, 
                language=None,  # Auto-detect language
                task="transcribe",  # Explicitly set task
                fp16=False,  # Use FP32 for better compatibility
                verbose=False  # Reduce console output
            )
            
            # Clean up temporary file
            try:
                os.unlink(audio_path)
            except:
                pass  # Ignore cleanup errors
            
            # Extract and validate transcribed text
            transcribed_text = result.get("text", "").strip()
            detected_language = result.get("language", "unknown")
            
            if not transcribed_text:
                return None, "No speech detected in audio"
            
            # Log detected language for debugging
            print(f"Whisper detected language: {detected_language}")
            print(f"Transcribed text: {transcribed_text}")
            
            return transcribed_text, None
            
        except Exception as e:
            # Make sure to clean up the file descriptor if something goes wrong
            try:
                os.close(fd)
                os.unlink(audio_path)
            except:
                pass
            raise e
        
    except Exception as e:
        error_msg = f"Error transcribing audio: {str(e)}"
        print(f"STT Error: {error_msg}")  # Debug logging
        return None, error_msg

def text_to_speech_fallback(text, language="english"):
    """Fallback TTS using system commands"""
    try:
        import subprocess
        import tempfile
        import os
        
        # Create temporary file for output
        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        # Try Windows SAPI (Speech API)
        if os.name == 'nt':  # Windows
            try:
                import pyttsx3
                engine = pyttsx3.init()
                
                # Set voice properties
                voices = engine.getProperty('voices')
                if voices:
                    # Try to find appropriate voice for language
                    for voice in voices:
                        if language == "arabic" and ("arabic" in voice.name.lower() or "ar" in voice.id.lower()):
                            engine.setProperty('voice', voice.id)
                            break
                        elif language == "english" and ("english" in voice.name.lower() or "en" in voice.id.lower()):
                            engine.setProperty('voice', voice.id)
                            break
                
                # Set speech rate and volume
                engine.setProperty('rate', 150)  # Speed of speech
                engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
                
                # Save to file
                engine.save_to_file(text, output_path)
                engine.runAndWait()
                
                # Read the generated file
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    with open(output_path, "rb") as f:
                        audio_content = f.read()
                    os.unlink(output_path)
                    return audio_content, None
                    
            except ImportError:
                pass  # pyttsx3 not available
            except Exception as e:
                pass  # Other errors with pyttsx3
        
        # Clean up if we get here
        try:
            os.unlink(output_path)
        except:
            pass
            
        return None, "No fallback TTS available"
        
    except Exception as e:
        return None, f"Fallback TTS error: {str(e)}"

def text_to_speech(text, language="english"):
    """Convert text to speech using PlayHT API with local models as fallback"""
    # Try PlayHT API first (highest quality)
    audio_content, error = text_to_speech_playht(text, language)
    
    if audio_content is not None:
        return audio_content, error
    
    # If PlayHT failed, try local TTS
    st.info("PlayHT TTS failed, trying local TTS...")
    audio_content, error = text_to_speech_local(text, language)
    
    if audio_content is not None:
        return audio_content, error
    
    # If both failed, try system fallback
    st.info("Local TTS also failed, trying system fallback TTS...")
    return text_to_speech_fallback(text, language)

def speech_to_text_openai_api(audio_bytes):
    """Fallback speech-to-text using OpenAI Whisper API"""
    try:
        import requests
        import tempfile
        import os
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None, "OpenAI API key not found. Please add OPENAI_API_KEY to your .env file."
        
        # Create temporary file
        fd, audio_path = tempfile.mkstemp(suffix=".wav")
        
        try:
            with os.fdopen(fd, 'wb') as tmp_file:
                tmp_file.write(audio_bytes)
            
            # Send to OpenAI Whisper API
            with open(audio_path, 'rb') as audio_file:
                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"file": audio_file},
                    data={"model": "whisper-1", "language": "auto"}  # Auto-detect language
                )
            
            if response.status_code == 200:
                result = response.json()
                transcribed_text = result.get("text", "").strip()
                return transcribed_text, None
            else:
                return None, f"OpenAI API error: {response.status_code}"
                
        finally:
            try:
                os.unlink(audio_path)
            except:
                pass
                
    except Exception as e:
        return None, f"OpenAI Whisper API error: {str(e)}"

def speech_to_text(audio_bytes):
    """Convert speech to text using local models with OpenAI API fallback"""
    # Try local Whisper first
    transcribed_text, error = speech_to_text_local(audio_bytes)
    
    if transcribed_text is not None:
        return transcribed_text, error
    
    # If local failed, try OpenAI API as fallback
    print("Local STT failed, trying OpenAI Whisper API...")
    return speech_to_text_openai_api(audio_bytes)

def create_audio_player(audio_content):
    """Create an audio player for the generated speech"""
    if audio_content:
        try:
            # Encode audio content to base64
            audio_base64 = base64.b64encode(audio_content).decode()
            # Create HTML audio player
            audio_html = f"""
            <audio controls autoplay>
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
                <source src="data:audio/mpeg;base64,{audio_base64}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            """
            return audio_html
        except Exception as e:
            st.error(f"Error creating audio player: {str(e)}")
            return None
    return None

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF document"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks"""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk) >= 200:  # Avoid very small chunks
            chunks.append(chunk)
    return chunks

def create_vectorizer(chunks):
    """Create TF-IDF vectorizer and document vectors"""
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(chunks)
    return vectorizer, vectors

def get_most_relevant_chunks(query, top_k=3):
    """Find most relevant chunks for the query"""
    global VECTORIZER, VECTORS, CHUNKS
    
    if VECTORIZER is None or VECTORS is None:
        return []
        
    # Vectorize the query
    query_vector = VECTORIZER.transform([query])
    
    # Calculate similarity
    similarities = cosine_similarity(query_vector, VECTORS).flatten()
    
    # Get indices of top k chunks
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    # Return relevant chunks
    return [CHUNKS[i] for i in top_indices if similarities[i] > 0.1]

def check_rate_limit():
    """Check if the user is within rate limits. Returns (allowed, message)."""
    import time
    from datetime import date
    
    # Initialize session counters
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
    if "last_query_time" not in st.session_state:
        st.session_state.last_query_time = 0
    
    # Initialize global daily counter (shared file-based)
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
    
    # Check per-session limit
    if st.session_state.query_count >= MAX_QUERIES_PER_SESSION:
        return False, f"Session limit reached ({MAX_QUERIES_PER_SESSION} queries). Please refresh the page to start a new session."
    
    # Check global daily limit
    if daily_data["count"] >= MAX_QUERIES_PER_DAY_GLOBAL:
        return False, "Daily usage limit reached. Please try again tomorrow."
    
    # Check cooldown
    elapsed = time.time() - st.session_state.last_query_time
    if elapsed < COOLDOWN_SECONDS:
        wait = int(COOLDOWN_SECONDS - elapsed) + 1
        return False, f"Please wait {wait} seconds between queries."
    
    # Update counters
    st.session_state.query_count += 1
    st.session_state.last_query_time = time.time()
    daily_data["count"] += 1
    
    try:
        with open(counter_file, "w") as f:
            json.dump(daily_data, f)
    except Exception:
        pass  # Non-critical if file write fails
    
    return True, None

def query_openrouter(query, context, model="openai/gpt-3.5-turbo", temperature=0.7, max_tokens=800):
    """Query OpenRouter API with the question and context"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        return "Error: OpenRouter API key not found in .env file. Please create a .env file with your OPENROUTER_API_KEY."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://farmerschatbot.com",
        "X-Title": "Lebanese Agricultural Guide Chatbot"
    }
    
    # Detect the language of the query
    query_language = detect_language(query)
    
    # Create concise, effective prompt
    if query_language == "arabic":
        prompt = f"""أنت خبير زراعي متخصص في الزراعة اللبنانية. أجب باللغة العربية بناءً على المعلومات المقدمة.

السياق من الدليل الزراعي اللبناني:
{context}

السؤال: {query}

قدم إجابة شاملة ومفصلة تتضمن الحقائق والبيانات ذات الصلة من السياق. إذا لم تكن المعلومات كافية، اذكر ذلك واستخدم المبادئ الزراعية العامة مع التوضيح."""

    else:
        prompt = f"""You are an expert agricultural advisor specializing in Lebanese farming. Provide a comprehensive answer based on the given information.

Context from Lebanese Agricultural Guide:
{context}

Question: {query}

Provide a detailed answer using relevant facts and data from the context. If information is insufficient, acknowledge this and apply general agricultural principles while clearly indicating what's not from the guide."""
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(
            OPENROUTER_API_URL, 
            headers=headers, 
            data=json.dumps(payload),
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            try:
                return response_data['choices'][0]['message']['content']
            except (KeyError, IndexError, TypeError):
                return "Error: Unexpected response format from API."
        else:
            return f"Error: Failed to get response from API. Status code: {response.status_code}. Response: {response.text}"
    except requests.exceptions.ConnectionError:
        return "Network error: Unable to connect to the OpenRouter API. Please check your internet connection or try again later."
    except requests.exceptions.Timeout:
        return "Request timed out. The OpenRouter API is taking too long to respond. Please try again later."
    except Exception as e:
        return f"Error querying the API: {str(e)}"

def simple_answer_from_context(query, context):
    """Provide a simple answer when API is unavailable"""
    # Detect the language of the query
    query_language = detect_language(query)
    
    # Convert query and context to lowercase for easier matching
    query_lower = query.lower()
    context_lower = context.lower()
    
    # Extract sentences that might contain relevant information
    sentences = [s.strip() for s in context.split('.') if s.strip()]
    relevant_sentences = [s for s in sentences if any(term in s.lower() for term in query_lower.split())]
    
    if relevant_sentences:
        if query_language == "arabic":
            return "\n\n".join([
                "إليك الأقسام ذات الصلة من الدليل الزراعي:",
                *relevant_sentences[:5]
            ])
        else:
            return "\n\n".join([
                "Here are the relevant sections from the agricultural guide:",
                *relevant_sentences[:5]
            ])
    else:
        if query_language == "arabic":
            return "لم يتم العثور على تطابقات دقيقة في الوثيقة. يرجى تجربة سؤال مختلف أو التحقق من اتصالك بالإنترنت لاستخدام الإجابة المدعومة بالذكاء الاصطناعي."
        else:
            return "No exact matches found in the document. Please try a different question or check your internet connection to use the AI-powered answer."

def get_playht_voices():
    """Get available PlayHT voices"""
    global PLAYHT_CLIENT
    
    if not PLAYHT_AVAILABLE or PLAYHT_CLIENT is None:
        return []
    
    try:
        # Note: The pyht SDK doesn't have a direct get_voices method
        # You would need to use the REST API directly or check your PlayHT dashboard
        # For now, return some common voice IDs
        common_voices = [
            {
                "id": "s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json",
                "name": "Female English (CS)",
                "language": "English"
            },
            {
                "id": "s3://voice-cloning-zero-shot/775ae416-49bb-4fb6-bd45-740f205d20a1/jennifersaad/manifest.json", 
                "name": "Jennifer (Arabic/English)",
                "language": "Arabic/English"
            }
        ]
        return common_voices
    except Exception as e:
        print(f"Error getting PlayHT voices: {str(e)}")
        return []

def text_to_speech_playht(text, language="english"):
    """Convert text to speech using PlayHT API"""
    global PLAYHT_CLIENT
    
    if not PLAYHT_AVAILABLE or PLAYHT_CLIENT is None:
        return None, "PlayHT client not available. Please install pyht: pip install pyht"
    
    try:
        # Import TTSOptions here to avoid import errors
        from pyht.client import TTSOptions
        
        # Select appropriate voice based on language
        if language == "arabic":
            # Arabic voice - you may need to adjust this based on available voices in your account
            voice_id = "s3://voice-cloning-zero-shot/775ae416-49bb-4fb6-bd45-740f205d20a1/jennifersaad/manifest.json"
            voice_engine = "Play3.0-mini-http"  # Use the latest model
        else:
            # English voice - high-quality option
            voice_id = "s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json"
            voice_engine = "Play3.0-mini-http"  # Use the latest model
        
        # Create TTS options
        options = TTSOptions(
            voice=voice_id,
            format="FORMAT_WAV",
            sample_rate=24000,
            speed=1.0,
            language="ARABIC" if language == "arabic" else "ENGLISH"
        )
        
        # Generate speech using PlayHT
        audio_chunks = []
        for chunk in PLAYHT_CLIENT.tts(text, options, voice_engine=voice_engine):
            audio_chunks.append(chunk)
        
        # Combine all chunks into a single audio file
        audio_content = b''.join(audio_chunks)
        
        return audio_content, None
        
    except Exception as e:
        return None, f"PlayHT TTS error: {str(e)}"

def main():
    st.title("Agricultural Guide for Lebanon - Chatbot")
    
    global DOCUMENT_TEXT, CHUNKS, VECTORIZER, VECTORS
    
    # Check if PDF file exists
    if not os.path.exists(PDF_PATH):
        st.error(f"Error: '{PDF_PATH}' not found. Please make sure the file exists in the project directory.")
        return
    
    # Initialize or load document (cached — only runs once)
    DOCUMENT_TEXT, CHUNKS, VECTORIZER, VECTORS = _load_and_process_pdf(PDF_PATH)
    
    # Load local models for voice features (cached — only runs once)
    load_local_models()
    
    # Display voice model status
    col1, col2, col3 = st.columns(3)
    with col1:
        if PLAYHT_AVAILABLE and PLAYHT_CLIENT is not None:
            st.success("🎙️ PlayHT TTS: Ready")
        elif TTS_AVAILABLE and TTS_MODEL is not None:
            st.success("🔊 Local TTS: Ready")
        else:
            st.warning("🔊 TTS: Install with `pip install TTS pyht`")
    
    with col2:
        if WHISPER_AVAILABLE and WHISPER_MODEL is not None:
            st.success("🎤 Local STT: Ready")
        else:
            st.warning("🎤 STT: Install with `pip install openai-whisper`")
    
    with col3:
        # Show which TTS method will be used
        if PLAYHT_AVAILABLE and PLAYHT_CLIENT is not None:
            st.info("🚀 Using PlayHT (Premium)")
        elif TTS_AVAILABLE and TTS_MODEL is not None:
            st.info("🏠 Using Local TTS")
        else:
            st.info("⚙️ Using System TTS")
    
    # Sidebar for configuration
    st.sidebar.title("Chatbot Settings")
    
    # Debug section
    with st.sidebar.expander("🔧 Debug Info"):
        st.write("**Speech-to-Text Status:**")
        if WHISPER_AVAILABLE and WHISPER_MODEL is not None:
            st.success("✅ Local Whisper: Ready")
        else:
            st.error("❌ Local Whisper: Not available")
            
        # Check OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            st.success("✅ OpenAI API: Key found")
        else:
            st.warning("⚠️ OpenAI API: No key found")
            
        st.write("**Text-to-Speech Status:**")
        if PLAYHT_AVAILABLE and PLAYHT_CLIENT is not None:
            st.success("✅ PlayHT TTS: Ready")
        else:
            st.error("❌ PlayHT TTS: Not available")
            
        if TTS_AVAILABLE and TTS_MODEL is not None:
            st.success("✅ Local TTS: Ready")
        else:
            st.error("❌ Local TTS: Not available")
            
        # PlayHT API credentials
        playht_user_id = os.getenv("PLAYHT_USER_ID")
        playht_api_key = os.getenv("PLAYHT_API_KEY")
        if playht_user_id and playht_api_key:
            st.success("✅ PlayHT API: Credentials found")
        else:
            st.warning("⚠️ PlayHT API: Missing credentials")
            
        # OpenRouter API key
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            st.success("✅ OpenRouter API: Key found")
        else:
            st.warning("⚠️ OpenRouter API: No key found")
    
    # TTS Method Selection
    st.sidebar.write("**TTS Priority:**")
    st.sidebar.info("1. PlayHT API (Highest Quality)\n2. Local TTS\n3. System Fallback")
    
    # Voice Testing Section
    if PLAYHT_AVAILABLE and PLAYHT_CLIENT is not None:
        with st.sidebar.expander("🎙️ Test PlayHT Voice"):
            test_text = st.text_input("Test text:", value="Hello, this is a voice test.")
            test_language = st.selectbox("Language:", ["english", "arabic"])
            
            if st.button("🔊 Test Voice"):
                with st.spinner("Generating test audio..."):
                    audio_content, error = text_to_speech_playht(test_text, test_language)
                    if error:
                        st.error(f"Voice test failed: {error}")
                    else:
                        st.success("Voice test successful!")
                        audio_html = create_audio_player(audio_content)
                        if audio_html:
                            st.markdown(audio_html, unsafe_allow_html=True)
    
    # Model selection — only cost-effective models for public deployment
    model_options = {
        "GPT-3.5 Turbo": "openai/gpt-3.5-turbo",
        "Claude 3 Haiku": "anthropic/claude-3-haiku-20240307",
        "Llama 3 70B": "meta-llama/llama-3-70b-instruct",
    }
    
    selected_model_name = st.sidebar.selectbox(
        "Select AI Model:",
        list(model_options.keys()),
        index=0
    )
    selected_model = model_options[selected_model_name]
    
    # Temperature slider
    temperature = st.sidebar.slider(
        "Temperature (Higher = More Creative):",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1
    )
    
    # Response length slider (capped to control costs)
    max_tokens = st.sidebar.slider(
        "Maximum Response Length:",
        min_value=200,
        max_value=800,
        value=800,
        step=100
    )
    
    # Display usage counter in sidebar
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
    remaining = MAX_QUERIES_PER_SESSION - st.session_state.query_count
    st.sidebar.write("---")
    st.sidebar.write(f"**Queries remaining:** {remaining}/{MAX_QUERIES_PER_SESSION}")
    
    # Query input
    st.write("Ask any question about Lebanese agriculture:")
    
    # Create columns for text input and voice recording
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input("Your question")
    
    with col2:
        st.write("🎤 **Voice Input**")
        audio_bytes = audio_recorder(
            text="Record",
            recording_color="#e74c3c",
            neutral_color="#34495e",
            icon_name="microphone",
            icon_size="2x",
        )
    
    # Process voice input if available
    if audio_bytes:
        # Debug: Show audio data info
        st.info(f"Audio data received: {len(audio_bytes)} bytes")
        
        # Validate audio data
        if len(audio_bytes) < 1000:  # Minimum reasonable audio size
            st.warning("Audio recording seems too short. Please try recording for at least 2-3 seconds.")
        else:
            with st.spinner("Transcribing audio..."):
                try:
                    transcribed_text, error = speech_to_text(audio_bytes)
                    
                    if error:
                        st.error(f"Speech-to-text error: {error}")
                        st.info("💡 Tips for better speech recognition:")
                        st.info("• Speak clearly and at a moderate pace")
                        st.info("• Ensure good microphone quality")
                        st.info("• Record in a quiet environment")
                        st.info("• Try speaking in either Arabic or English")
                    else:
                        if transcribed_text and transcribed_text.strip():
                            # Detect language of transcribed text
                            detected_lang = detect_language(transcribed_text)
                            lang_emoji = "🇦🇪" if detected_lang == "arabic" else "🇺🇸"
                            
                            query = transcribed_text
                            st.success(f"{lang_emoji} Transcribed ({detected_lang}): {transcribed_text}")
                        else:
                            st.warning("No speech detected. Please try again with clearer audio.")
                            
                except Exception as e:
                    st.error(f"Unexpected error during transcription: {str(e)}")
                    st.info("Please try recording again or use text input instead.")

    if query:
        # Detect language for UI messages
        query_language = detect_language(query)
        
        if query_language == "arabic":
            search_message = "البحث عن إجابة..."
            answer_header = "### الإجابة"
            fallback_header = "### إجابة احتياطية (مطابقة نص أساسية)"
            no_info_message = "لم يتم العثور على معلومات ذات صلة في الدليل الزراعي."
            model_info = f"*تم إنشاء الإجابة باستخدام: {selected_model_name}*"
        else:
            search_message = "Searching for answer..."
            answer_header = "### Answer"
            fallback_header = "### Fallback Answer (Basic Text Matching)"
            no_info_message = "No relevant information found in the agricultural guide."
            model_info = f"*Answer generated using: {selected_model_name}*"
        
        # Check rate limit before calling API
        allowed, limit_msg = check_rate_limit()
        if not allowed:
            st.warning(f"⏳ {limit_msg}")
            st.stop()
        
        with st.spinner(search_message):
            # Get relevant document chunks
            relevant_chunks = get_most_relevant_chunks(query)
            
            if relevant_chunks:
                # Join chunks into a single context
                context = "\n\n".join(relevant_chunks)
                
                # Get answer from OpenRouter API
                answer = query_openrouter(query, context, selected_model, temperature, max_tokens)
                
                # Check if there was an API error
                if any(answer.startswith(p) for p in ["Error", "Network error", "Request timed out"]):
                    st.error(answer)
                    st.write(fallback_header)
                    fallback_answer = simple_answer_from_context(query, context)
                    st.write(fallback_answer)
                    
                    # Add Text-to-Speech for fallback answer
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("🔊 Listen", key="tts_fallback_button"):
                            with st.spinner("Generating speech..."):
                                audio_content, tts_error = text_to_speech(fallback_answer, query_language)
                                if tts_error:
                                    st.error(f"Text-to-speech error: {tts_error}")
                                else:
                                    audio_html = create_audio_player(audio_content)
                                    if audio_html:
                                        st.markdown(audio_html, unsafe_allow_html=True)
                else:
                    st.write(answer_header)
                    st.write(answer)
                    
                    # Add Text-to-Speech functionality
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("🔊 Listen", key="tts_button"):
                            with st.spinner("Generating speech..."):
                                audio_content, tts_error = text_to_speech(answer, query_language)
                                if tts_error:
                                    st.error(f"Text-to-speech error: {tts_error}")
                                else:
                                    audio_html = create_audio_player(audio_content)
                                    if audio_html:
                                        st.markdown(audio_html, unsafe_allow_html=True)
                    
                    # Display model information
                    st.write("---")
                    st.write(model_info)
            else:
                st.write(no_info_message)

if __name__ == "__main__":
    main()
