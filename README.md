# Lebanese Agricultural Guide RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that provides expert agricultural advice for Lebanese farming practices with **local** voice capabilities - no API keys required for voice features!

## Features

### 🤖 AI-Powered Responses
- **Multi-language Support**: Automatically detects and responds in Arabic or English
- **Multiple LLM Options**: Choose from GPT-3.5/4, Claude, Llama, Mistral models
- **RAG Technology**: Retrieves relevant information from Lebanese Agricultural Guide PDF

### 🎤 Local Voice Input (Speech-to-Text)
- **Real-time Recording**: Record questions directly in the browser
- **Multi-language Recognition**: Supports both Arabic and English speech
- **Powered by OpenAI Whisper**: Industry-leading speech recognition accuracy
- **100% Local**: No internet connection required for voice processing

### 🔊 Local Voice Output (Text-to-Speech)
- **Human-like Voices**: High-quality, natural-sounding speech synthesis
- **Language-Aware**: Automatically selects appropriate voice for Arabic or English
- **Powered by XTTS-v2**: State-of-the-art local voice generation technology
- **No API Keys**: Completely offline voice synthesis

### 🌐 Bilingual Interface
- **Complete Arabic/English Support**: All UI elements in both languages
- **Smart Language Detection**: Automatically adapts interface based on query language
- **Cultural Sensitivity**: Proper Arabic text rendering and layout

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Farmers_Chatbot_V2
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API key (only for LLM responses)**
   Create a `.env` file in the project root with:
   ```env
   # OpenRouter API Key for LLM responses (required)
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

4. **Add the Agricultural Guide PDF**
   Place `Agricultural Guide for Lebanon.pdf` in the project root directory.

5. **Run the application**
   ```bash
   streamlit run rag_chatbot.py
   ```

## Local Voice Setup

### Automatic Installation
The voice models will be automatically downloaded and loaded when you first use the voice features:

- **XTTS-v2**: ~2GB download for text-to-speech
- **Whisper Base**: ~290MB download for speech-to-text

### Manual Installation (Optional)
If you want to pre-install the voice models:

```bash
# For Text-to-Speech
python -c "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2')"

# For Speech-to-Text  
python -c "import whisper; whisper.load_model('base')"
```

## API Keys Setup

### OpenRouter API Key (Required for LLM responses)
1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for an account
3. Navigate to API Keys section
4. Generate a new API key
5. Add to your `.env` file

**Note**: Voice features work completely offline and don't require any API keys!

## Usage

### Text Input
1. Type your question in Arabic or English in the text input field
2. The chatbot will automatically detect the language and respond accordingly

### Voice Input (Local)
1. Click the "Record / تسجيل" button
2. Speak your question clearly
3. The system will transcribe your speech locally using Whisper
4. No internet connection required for transcription

### Voice Output (Local)
1. After receiving a text response, click "🔊 Listen / استمع"
2. The system will generate natural speech locally using XTTS-v2
3. Audio will play automatically with playback controls
4. No internet connection required for speech generation

## Technical Architecture

### RAG Pipeline
1. **Document Ingestion**: Extract text from PDF and split into chunks
2. **Vectorization**: Create TF-IDF embeddings for semantic search
3. **Retrieval**: Find most relevant document chunks based on query
4. **Generation**: Send retrieved context + query to LLM for comprehensive answers
5. **Local Voice Processing**: Convert between speech and text using local models

### Local Voice Technologies
- **Speech-to-Text**: OpenAI Whisper (local) for accurate transcription
- **Text-to-Speech**: XTTS-v2 (local) for human-like voice synthesis
- **Language Detection**: Unicode-based Arabic/English detection
- **Audio Processing**: Real-time browser-based recording and playback

## Supported Languages

- **Arabic**: Full support including various dialects
- **English**: Complete support with natural pronunciation

## Model Options

### LLM Models (via OpenRouter - requires API key)
- GPT-3.5 Turbo
- GPT-4o
- Claude 3 (Haiku, Sonnet, Opus)
- Llama 3 70B
- Mistral Large

### Local Voice Models (no API keys required)
- **Arabic TTS**: XTTS-v2 multilingual voices optimized for Arabic
- **English TTS**: High-quality English voices with natural intonation
- **STT**: OpenAI Whisper with automatic language detection

## Configuration Options

### Sidebar Controls
- **Model Selection**: Choose your preferred LLM
- **Temperature**: Adjust creativity (0.0 = focused, 1.0 = creative)
- **Response Length**: Control maximum response length (300-1500 tokens)

## System Requirements

### Minimum Requirements
- **RAM**: 4GB (8GB recommended)
- **Storage**: 3GB free space for voice models
- **CPU**: Modern multi-core processor
- **Internet**: Required only for LLM responses, not for voice features

### Recommended Requirements
- **RAM**: 8GB or more
- **GPU**: NVIDIA GPU with 4GB+ VRAM (optional, for faster processing)
- **Storage**: 5GB free space
- **Internet**: Stable connection for LLM API calls

## Troubleshooting

### Common Issues

1. **Voice models not loading**
   - Ensure sufficient disk space (3GB+)
   - Check internet connection for initial model download
   - Restart the application if models fail to load

2. **Audio not recording**
   - Ensure microphone permissions are granted
   - Check browser compatibility (Chrome/Firefox recommended)

3. **LLM API errors**
   - Verify OpenRouter API key is correctly set in `.env` file
   - Check API key validity and quotas

4. **PDF not loading**
   - Ensure `Agricultural Guide for Lebanon.pdf` is in the project root
   - Check file permissions and format

### Performance Tips
- **GPU Acceleration**: If you have an NVIDIA GPU, the voice models will automatically use it for faster processing
- **Model Size**: The current setup uses balanced models (Whisper Base, XTTS-v2). For faster processing on lower-end hardware, you can modify the code to use smaller models
- **Memory Management**: Close other applications if you experience memory issues

## Privacy & Security

- **Local Voice Processing**: All voice features work completely offline
- **No Voice Data Transmission**: Your voice recordings never leave your computer
- **API Usage**: Only text queries are sent to LLM APIs, never audio data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Coqui AI**: For XTTS-v2 text-to-speech technology
- **OpenAI**: For Whisper speech-to-text capabilities
- **OpenRouter**: For access to multiple LLM providers
- **Streamlit**: For the web application framework

## Author

**Nizar Shehayeb**

For questions or support, please open an issue in the repository. 