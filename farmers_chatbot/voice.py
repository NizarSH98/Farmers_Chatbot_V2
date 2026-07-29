"""Optional voice adapters with explicit local/online boundaries."""

from __future__ import annotations

import asyncio
import os
import tempfile
from functools import lru_cache
from pathlib import Path

try:
    import edge_tts

    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import whisper

    LOCAL_WHISPER_AVAILABLE = True
except ImportError:
    LOCAL_WHISPER_AVAILABLE = False


@lru_cache(maxsize=1)
def _whisper_model():
    if not LOCAL_WHISPER_AVAILABLE:
        raise RuntimeError("Local Whisper is not installed")
    model_name = os.getenv("WHISPER_MODEL", "base")
    return whisper.load_model(model_name)


def transcribe_local(audio_bytes: bytes, language: str | None = None) -> str:
    """Transcribe browser-recorded audio with a local Whisper model."""

    if not LOCAL_WHISPER_AVAILABLE:
        raise RuntimeError("Local Whisper is not installed")
    temp_path: Path | None = None
    try:
        descriptor, raw_path = tempfile.mkstemp(suffix=".wav")
        os.close(descriptor)
        temp_path = Path(raw_path)
        temp_path.write_bytes(audio_bytes)
        language_code = {"arabic": "ar", "english": "en"}.get(language or "")
        result = _whisper_model().transcribe(
            str(temp_path),
            language=language_code,
            fp16=False,
        )
        return str(result.get("text", "")).strip()
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


async def _edge_generate(text: str, voice: str, path: str) -> None:
    communicator = edge_tts.Communicate(text, voice)
    await communicator.save(path)


def synthesize_edge(text: str, language: str) -> bytes:
    """Generate online TTS through Microsoft Edge voices.

    This is not an offline or local-privacy feature. The UI must disclose that the
    answer text is sent to the online TTS provider.
    """

    if not EDGE_TTS_AVAILABLE:
        raise RuntimeError("Online Edge TTS is not installed")
    voice = "ar-SA-HamedNeural" if language == "arabic" else "en-US-JennyNeural"
    temp_path: Path | None = None
    try:
        descriptor, raw_path = tempfile.mkstemp(suffix=".mp3")
        os.close(descriptor)
        temp_path = Path(raw_path)
        asyncio.run(_edge_generate(text, voice, str(temp_path)))
        audio = temp_path.read_bytes()
        if not audio:
            raise RuntimeError("TTS provider returned empty audio")
        return audio
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)

