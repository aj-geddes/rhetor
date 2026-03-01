"""SAPI TTS engine — Windows system voices via pyttsx3."""

from __future__ import annotations

import contextlib
import logging
import tempfile
from pathlib import Path
from typing import Any

from constants import SAPI_BASE_WPM
from tts.base_engine import TTSEngineNotAvailableError, TTSSynthesisError
from tts.models import AudioFormat, SynthesisResult, VoiceInfo

log = logging.getLogger(__name__)

try:
    import pyttsx3  # type: ignore[import-untyped]

    _PYTTSX3_AVAILABLE = True
except ImportError:
    _PYTTSX3_AVAILABLE = False


class SapiTTSEngine:
    """Tier 3 TTS engine using Windows SAPI5 voices via pyttsx3."""

    def __init__(self) -> None:
        self._engine: Any = None

    @property
    def engine_type(self) -> str:
        return "sapi"

    @property
    def is_available(self) -> bool:
        if not _PYTTSX3_AVAILABLE:
            return False
        try:
            self._ensure_engine()
            return True
        except TTSEngineNotAvailableError:
            return False

    def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        volume: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text via pyttsx3 save_to_file. Returns WAV audio bytes."""
        if not _PYTTSX3_AVAILABLE:
            raise TTSEngineNotAvailableError("pyttsx3 library is not installed")

        if not text.strip():
            raise TTSSynthesisError("Cannot synthesize empty text")

        engine = self._ensure_engine()

        try:
            engine.setProperty("voice", voice_id)
            engine.setProperty("rate", int(SAPI_BASE_WPM * speed))
            engine.setProperty("volume", volume)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            engine.save_to_file(text, str(tmp_path))
            engine.runAndWait()

            audio_data = tmp_path.read_bytes()
        except TTSSynthesisError:
            raise
        except Exception as exc:
            raise TTSSynthesisError(f"SAPI synthesis failed: {exc}") from exc
        finally:
            with contextlib.suppress(NameError, OSError):
                tmp_path.unlink(missing_ok=True)

        if not audio_data:
            raise TTSSynthesisError("SAPI returned empty audio data")

        return SynthesisResult(
            audio_data=audio_data,
            audio_format=AudioFormat.WAV,
            sample_rate=22050,
            sample_width=2,
            channels=1,
        )

    def get_voices(self) -> list[VoiceInfo]:
        """Discover installed SAPI5 voices and return VoiceInfo descriptors."""
        try:
            engine = self._ensure_engine()
        except TTSEngineNotAvailableError:
            return []

        voices = engine.getProperty("voices")
        result: list[VoiceInfo] = []
        for voice in voices:
            short_name = voice.id.split("\\")[-1].lower()
            voice_id = f"sapi-{short_name}"
            result.append(
                VoiceInfo(
                    voice_id=voice_id,
                    name=voice.name,
                    engine="sapi",
                    engine_voice_id=voice.id,
                    gender="",
                    language="en",
                    accent="",
                    description=f"System voice: {voice.name}",
                    requires_internet=False,
                )
            )
        return result

    def _ensure_engine(self) -> Any:
        """Lazily initialize the pyttsx3 engine."""
        if self._engine is None:
            try:
                self._engine = pyttsx3.init()
            except Exception as exc:
                raise TTSEngineNotAvailableError(
                    f"Failed to initialize pyttsx3: {exc}"
                ) from exc
        return self._engine
