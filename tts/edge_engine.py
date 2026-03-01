"""Edge TTS engine — online Microsoft neural voices via edge-tts library."""

from __future__ import annotations

import asyncio
import logging
import socket
from io import BytesIO

from constants import CONNECTIVITY_TIMEOUT_S
from tts.base_engine import TTSEngineNotAvailableError, TTSSynthesisError
from tts.models import AudioFormat, SynthesisResult, VoiceInfo
from tts.voice_catalog import VoiceCatalog

log = logging.getLogger(__name__)

try:
    import edge_tts

    _EDGE_AVAILABLE = True
except ImportError:
    _EDGE_AVAILABLE = False


class EdgeTTSEngine:
    """Tier 1 TTS engine using Microsoft's free neural voices (online)."""

    @property
    def engine_type(self) -> str:
        return "edge"

    @property
    def is_available(self) -> bool:
        return _EDGE_AVAILABLE and self._check_connectivity()

    def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        volume: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text using edge-tts. Returns MP3 audio bytes."""
        if not _EDGE_AVAILABLE:
            raise TTSEngineNotAvailableError("edge-tts library is not installed")

        if not text.strip():
            raise TTSSynthesisError("Cannot synthesize empty text")

        rate_str = self._speed_to_rate_string(speed)
        volume_str = self._volume_to_string(volume)

        try:
            audio_data = asyncio.run(
                self._synthesize_async(text, voice_id, rate_str, volume_str)
            )
        except TTSSynthesisError:
            raise
        except Exception as exc:
            raise TTSSynthesisError(f"Edge TTS synthesis failed: {exc}") from exc

        return SynthesisResult(
            audio_data=audio_data,
            audio_format=AudioFormat.MP3,
            sample_rate=24000,
            sample_width=2,
            channels=1,
        )

    def get_voices(self) -> list[VoiceInfo]:
        """Return curated edge voices from the catalog."""
        catalog = VoiceCatalog()
        return catalog.get_voices_for_engine("edge")

    @staticmethod
    async def _synthesize_async(
        text: str,
        voice_id: str,
        rate: str,
        volume: str,
    ) -> bytes:
        """Run edge-tts synthesis in an async context."""
        communicate = edge_tts.Communicate(text, voice_id, rate=rate, volume=volume)
        buffer = BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        audio_data = buffer.getvalue()
        if not audio_data:
            raise TTSSynthesisError("Edge TTS returned no audio data")
        return audio_data

    @staticmethod
    def _speed_to_rate_string(speed: float) -> str:
        """Convert speed multiplier (e.g. 1.25) to edge-tts rate string ('+25%')."""
        percent = round((speed - 1.0) * 100)
        if percent >= 0:
            return f"+{percent}%"
        return f"{percent}%"

    @staticmethod
    def _volume_to_string(volume: float) -> str:
        """Convert volume (0.0–1.0) to edge-tts volume string ('-20%', '+0%', etc.)."""
        percent = round((volume - 1.0) * 100)
        if percent >= 0:
            return f"+{percent}%"
        return f"{percent}%"

    @staticmethod
    def _check_connectivity() -> bool:
        """Check if the edge-tts speech service is reachable."""
        try:
            sock = socket.create_connection(
                ("speech.platform.bing.com", 443),
                timeout=CONNECTIVITY_TIMEOUT_S,
            )
            sock.close()
            return True
        except OSError:
            return False
