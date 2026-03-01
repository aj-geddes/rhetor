"""Curated voice catalog with lookup, filtering, and dynamic registration."""

from __future__ import annotations

from tts.models import VoiceInfo

# ── Curated Voices ───────────────────────────────────────────────────────────

_CURATED_VOICES: tuple[VoiceInfo, ...] = (
    # Edge TTS — Microsoft neural voices (online)
    VoiceInfo(
        voice_id="jenny-us",
        name="Jenny (US)",
        engine="edge",
        engine_voice_id="en-US-JennyNeural",
        gender="female",
        language="en",
        accent="US",
        description="Friendly, clear American female voice",
        requires_internet=True,
    ),
    VoiceInfo(
        voice_id="guy-us",
        name="Guy (US)",
        engine="edge",
        engine_voice_id="en-US-GuyNeural",
        gender="male",
        language="en",
        accent="US",
        description="Natural, warm American male voice",
        requires_internet=True,
    ),
    VoiceInfo(
        voice_id="aria-us",
        name="Aria (US)",
        engine="edge",
        engine_voice_id="en-US-AriaNeural",
        gender="female",
        language="en",
        accent="US",
        description="Expressive American female voice",
        requires_internet=True,
    ),
    VoiceInfo(
        voice_id="andrew-us",
        name="Andrew (US)",
        engine="edge",
        engine_voice_id="en-US-AndrewNeural",
        gender="male",
        language="en",
        accent="US",
        description="Professional American male voice",
        requires_internet=True,
    ),
    VoiceInfo(
        voice_id="sonia-gb",
        name="Sonia (GB)",
        engine="edge",
        engine_voice_id="en-GB-SoniaNeural",
        gender="female",
        language="en",
        accent="GB",
        description="Articulate British female voice",
        requires_internet=True,
    ),
    VoiceInfo(
        voice_id="ryan-gb",
        name="Ryan (GB)",
        engine="edge",
        engine_voice_id="en-GB-RyanNeural",
        gender="male",
        language="en",
        accent="GB",
        description="Clear British male voice",
        requires_internet=True,
    ),
    VoiceInfo(
        voice_id="natasha-au",
        name="Natasha (AU)",
        engine="edge",
        engine_voice_id="en-AU-NatashaNeural",
        gender="female",
        language="en",
        accent="AU",
        description="Warm Australian female voice",
        requires_internet=True,
    ),
    VoiceInfo(
        voice_id="william-au",
        name="William (AU)",
        engine="edge",
        engine_voice_id="en-AU-WilliamNeural",
        gender="male",
        language="en",
        accent="AU",
        description="Friendly Australian male voice",
        requires_internet=True,
    ),
    # Piper TTS — offline ONNX models
    VoiceInfo(
        voice_id="lessac-offline",
        name="Lessac (Offline)",
        engine="piper",
        engine_voice_id="en_US-lessac-medium",
        gender="male",
        language="en",
        accent="US",
        description="High-quality offline American voice",
        requires_internet=False,
    ),
    VoiceInfo(
        voice_id="amy-offline",
        name="Amy (Offline)",
        engine="piper",
        engine_voice_id="en_GB-amy-medium",
        gender="female",
        language="en",
        accent="GB",
        description="Clear offline British female voice",
        requires_internet=False,
    ),
    VoiceInfo(
        voice_id="alba-offline",
        name="Alba (Offline)",
        engine="piper",
        engine_voice_id="en_US-alba-medium",
        gender="female",
        language="en",
        accent="US",
        description="Natural offline American female voice",
        requires_internet=False,
    ),
)


class VoiceCatalog:
    """Registry of available TTS voices with lookup and filtering."""

    def __init__(self) -> None:
        self._voices: dict[str, VoiceInfo] = {v.voice_id: v for v in _CURATED_VOICES}

    def get_voice(self, voice_id: str) -> VoiceInfo | None:
        """Look up a voice by its friendly ID. Returns None if not found."""
        return self._voices.get(voice_id)

    def get_voices_for_engine(self, engine: str) -> list[VoiceInfo]:
        """Return all voices belonging to a specific engine type."""
        return [v for v in self._voices.values() if v.engine == engine]

    def get_all_voices(self) -> list[VoiceInfo]:
        """Return all registered voices."""
        return list(self._voices.values())

    def get_online_voices(self) -> list[VoiceInfo]:
        """Return voices that require an internet connection."""
        return [v for v in self._voices.values() if v.requires_internet]

    def get_offline_voices(self) -> list[VoiceInfo]:
        """Return voices that work without an internet connection."""
        return [v for v in self._voices.values() if not v.requires_internet]

    def register_voice(self, voice: VoiceInfo) -> None:
        """Add a voice to the catalog. Skips duplicates (same voice_id)."""
        if voice.voice_id not in self._voices:
            self._voices[voice.voice_id] = voice
