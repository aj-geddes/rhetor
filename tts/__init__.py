"""TTS engine abstraction — three-tier synthesis with automatic failover."""

from tts.base_engine import (
    TTSEngine,
    TTSEngineNotAvailableError,
    TTSError,
    TTSSynthesisError,
    TTSVoiceNotFoundError,
)
from tts.engine_manager import EngineManager
from tts.models import AudioFormat, SynthesisResult, VoiceInfo
from tts.voice_catalog import VoiceCatalog

__all__ = [
    "AudioFormat",
    "EngineManager",
    "SynthesisResult",
    "TTSEngine",
    "TTSEngineNotAvailableError",
    "TTSError",
    "TTSSynthesisError",
    "TTSVoiceNotFoundError",
    "VoiceCatalog",
    "VoiceInfo",
]
