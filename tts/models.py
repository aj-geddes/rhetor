"""TTS data models — audio format metadata and voice descriptors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class AudioFormat(Enum):
    """Audio encoding format produced by a TTS engine."""

    MP3 = auto()
    WAV = auto()
    PCM_RAW = auto()


@dataclass(frozen=True, slots=True)
class SynthesisResult:
    """Immutable result of a TTS synthesis call.

    Frozen for thread safety — produced by the TTS engine and consumed
    by the audio pipeline on a different thread.
    """

    audio_data: bytes
    audio_format: AudioFormat
    sample_rate: int
    sample_width: int = 2
    channels: int = 1


@dataclass(frozen=True, slots=True)
class VoiceInfo:
    """Descriptor for a TTS voice available in the system."""

    voice_id: str
    name: str
    engine: str
    engine_voice_id: str
    gender: str = ""
    language: str = "en"
    accent: str = ""
    description: str = ""
    requires_internet: bool = False
    preview_text: str = "Hello, I'm ready to read your documents."
