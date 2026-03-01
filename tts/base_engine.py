"""TTSEngine protocol and shared TTS exceptions."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from tts.models import SynthesisResult, VoiceInfo


class TTSError(Exception):
    """Base exception for TTS engine failures."""


class TTSEngineNotAvailableError(TTSError):
    """Raised when a TTS engine cannot be initialized (missing library, etc.)."""


class TTSSynthesisError(TTSError):
    """Raised when synthesis fails (network error, invalid voice, etc.)."""


class TTSVoiceNotFoundError(TTSError):
    """Raised when a requested voice ID is not recognized."""


@runtime_checkable
class TTSEngine(Protocol):
    """Structural protocol that all TTS engines must satisfy."""

    @property
    def engine_type(self) -> str:
        """Short identifier for this engine type (e.g. 'edge', 'piper', 'sapi')."""
        ...

    @property
    def is_available(self) -> bool:
        """Whether this engine is ready to synthesize (library present, runtime OK)."""
        ...

    def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        volume: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text to audio bytes.

        Args:
            text: The text to speak.
            voice_id: Engine-specific voice identifier.
            speed: Playback speed multiplier (0.5–2.0).
            volume: Volume level (0.0–1.0).

        Returns:
            SynthesisResult containing audio data and format metadata.

        Raises:
            TTSSynthesisError: If synthesis fails.
            TTSVoiceNotFoundError: If the voice_id is not recognized.
        """
        ...

    def get_voices(self) -> list[VoiceInfo]:
        """Return the list of voices this engine can use."""
        ...
