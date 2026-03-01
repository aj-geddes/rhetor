"""Piper TTS engine — offline ONNX neural voices via piper-tts library."""

from __future__ import annotations

import logging
import wave
from io import BytesIO
from pathlib import Path

from constants import ASSETS_DIR
from tts.base_engine import TTSEngineNotAvailableError, TTSSynthesisError
from tts.models import AudioFormat, SynthesisResult, VoiceInfo
from tts.voice_catalog import VoiceCatalog

log = logging.getLogger(__name__)

VOICES_DIR = ASSETS_DIR / "voices"

try:
    from piper import PiperVoice

    _PIPER_AVAILABLE = True
except ImportError:
    _PIPER_AVAILABLE = False


class PiperTTSEngine:
    """Tier 2 TTS engine using Piper's offline ONNX neural models."""

    def __init__(self) -> None:
        self._loaded_voices: dict[str, object] = {}

    @property
    def engine_type(self) -> str:
        return "piper"

    @property
    def is_available(self) -> bool:
        return _PIPER_AVAILABLE and self._has_any_models()

    def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        volume: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text using a Piper ONNX model. Returns WAV audio bytes."""
        if not _PIPER_AVAILABLE:
            raise TTSEngineNotAvailableError("piper-tts library is not installed")

        if not text.strip():
            raise TTSSynthesisError("Cannot synthesize empty text")

        model_path = self._resolve_model_path(voice_id)
        voice = self._get_or_load_voice(voice_id, model_path)

        length_scale = 1.0 / speed if speed > 0 else 1.0

        try:
            buffer = BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                voice.synthesize(  # type: ignore[union-attr]
                    text,
                    wav_file,
                    length_scale=length_scale,
                )
            audio_data = buffer.getvalue()
        except Exception as exc:
            raise TTSSynthesisError(f"Piper synthesis failed: {exc}") from exc

        return SynthesisResult(
            audio_data=audio_data,
            audio_format=AudioFormat.WAV,
            sample_rate=22050,
            sample_width=2,
            channels=1,
        )

    def get_voices(self) -> list[VoiceInfo]:
        """Return curated piper voices from the catalog."""
        catalog = VoiceCatalog()
        return catalog.get_voices_for_engine("piper")

    def _get_or_load_voice(self, voice_id: str, model_path: Path) -> object:
        """Load a Piper voice model, caching for reuse."""
        if voice_id not in self._loaded_voices:
            try:
                self._loaded_voices[voice_id] = PiperVoice.load(str(model_path))
                log.info("Loaded Piper model: %s", model_path.name)
            except Exception as exc:
                raise TTSSynthesisError(
                    f"Failed to load Piper model {model_path}: {exc}"
                ) from exc
        return self._loaded_voices[voice_id]

    @staticmethod
    def _resolve_model_path(voice_id: str) -> Path:
        """Map an engine voice ID to the .onnx model file path."""
        model_path = VOICES_DIR / f"{voice_id}.onnx"
        if not model_path.exists():
            raise TTSSynthesisError(f"Piper model not found: {model_path}")
        return model_path

    @staticmethod
    def _has_any_models() -> bool:
        """Check if any .onnx voice models are installed."""
        if not VOICES_DIR.exists():
            return False
        return any(VOICES_DIR.glob("*.onnx"))
