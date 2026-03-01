"""Engine manager — engine selection, failover, and voice resolution."""

from __future__ import annotations

import logging

from tts.base_engine import (
    TTSEngineNotAvailableError,
    TTSError,
    TTSSynthesisError,
)
from tts.edge_engine import EdgeTTSEngine
from tts.models import SynthesisResult, VoiceInfo
from tts.piper_engine import PiperTTSEngine
from tts.sapi_engine import SapiTTSEngine
from tts.voice_catalog import VoiceCatalog

log = logging.getLogger(__name__)

# Engine tier order for failover
_TIER_ORDER = ("edge", "piper", "sapi")


class EngineManager:
    """Manages TTS engine selection, failover, and voice resolution."""

    def __init__(self) -> None:
        self._engines: dict[str, EdgeTTSEngine | PiperTTSEngine | SapiTTSEngine] = {}
        self._active_engine: str | None = None
        self._catalog = VoiceCatalog()

    @property
    def active_engine(self) -> str | None:
        """The currently selected engine type, or None if not initialized."""
        return self._active_engine

    def initialize(
        self,
        preferred_engine: str = "auto",
        force_offline: bool = False,
    ) -> None:
        """Create engine instances and select the active engine.

        Args:
            preferred_engine: 'auto', 'edge', 'piper', or 'sapi'.
            force_offline: If True, skip edge-tts even if available.
        """
        self._engines = {
            "edge": EdgeTTSEngine(),
            "piper": PiperTTSEngine(),
            "sapi": SapiTTSEngine(),
        }

        # Register dynamically discovered SAPI voices
        sapi = self._engines["sapi"]
        if sapi.is_available:
            for voice in sapi.get_voices():
                self._catalog.register_voice(voice)

        # Select active engine
        if preferred_engine != "auto" and preferred_engine in self._engines:
            engine = self._engines[preferred_engine]
            if force_offline and preferred_engine == "edge":
                log.info("Skipping edge engine (force_offline=True)")
            elif engine.is_available:
                self._active_engine = preferred_engine
                log.info("Using preferred engine: %s", preferred_engine)
                return

        # Auto-select by tier order
        for engine_type in _TIER_ORDER:
            if force_offline and engine_type == "edge":
                continue
            engine = self._engines[engine_type]
            if engine.is_available:
                self._active_engine = engine_type
                log.info("Auto-selected engine: %s", engine_type)
                return

        raise TTSEngineNotAvailableError("No TTS engine is available")

    def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        volume: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text, resolving voice IDs and failing over on error.

        Args:
            text: Text to speak.
            voice_id: Friendly voice ID (e.g. 'jenny-us') — resolved to engine-specific ID.
            speed: Speed multiplier (0.5–2.0).
            volume: Volume level (0.0–1.0).

        Returns:
            SynthesisResult from the active (or failover) engine.
        """
        if self._active_engine is None:
            raise TTSEngineNotAvailableError("EngineManager not initialized")

        # Resolve friendly voice_id to engine-specific voice ID
        engine_voice_id = self._resolve_voice_id(voice_id, self._active_engine)

        # Try active engine first
        try:
            engine = self._engines[self._active_engine]
            return engine.synthesize(text, engine_voice_id, speed, volume)
        except TTSSynthesisError as exc:
            log.warning(
                "Synthesis failed on %s: %s — attempting failover",
                self._active_engine,
                exc,
            )

        # Failover through remaining tiers
        for engine_type in _TIER_ORDER:
            if engine_type == self._active_engine:
                continue
            engine = self._engines[engine_type]
            if not engine.is_available:
                continue

            failover_voice_id = self._pick_failover_voice(engine_type)
            try:
                result = engine.synthesize(text, failover_voice_id, speed, volume)
                self._active_engine = engine_type
                log.info("Failover succeeded with engine: %s", engine_type)
                return result
            except TTSError:
                log.warning("Failover also failed on %s", engine_type)
                continue

        raise TTSSynthesisError("All TTS engines failed to synthesize")

    def get_available_voices(self) -> list[VoiceInfo]:
        """Return catalog voices filtered to currently available engines."""
        available_engines = {
            etype for etype, engine in self._engines.items() if engine.is_available
        }
        return [v for v in self._catalog.get_all_voices() if v.engine in available_engines]

    def _resolve_voice_id(self, voice_id: str, engine_type: str) -> str:
        """Map a friendly voice ID to the engine-specific voice ID."""
        voice = self._catalog.get_voice(voice_id)
        if voice is not None:
            return voice.engine_voice_id
        # If not in catalog, assume it's already an engine-specific ID
        return voice_id

    def _pick_failover_voice(self, engine_type: str) -> str:
        """Choose a default engine-specific voice ID for failover."""
        voices = self._catalog.get_voices_for_engine(engine_type)
        if voices:
            return voices[0].engine_voice_id
        # Shouldn't happen for curated engines, but just in case
        return ""
