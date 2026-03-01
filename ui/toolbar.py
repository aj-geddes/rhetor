"""Toolbar — playback controls, voice selection, speed/volume sliders."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from constants import DEFAULT_SPEED, DEFAULT_VOLUME, MAX_SPEED, MIN_SPEED
from tts.models import VoiceInfo

if TYPE_CHECKING:
    from app import RhetorApp


class Toolbar(ctk.CTkFrame):
    """Playback control toolbar with buttons, voice dropdown, and sliders."""

    def __init__(self, master: ctk.CTkBaseClass, app: RhetorApp) -> None:
        super().__init__(master, height=48)
        self._app = app

        # ── Playback Buttons ─────────────────────────────────────────

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="left", padx=(8, 4))

        self._skip_back_btn = ctk.CTkButton(
            btn_frame, text="<<", width=40, command=self._on_skip_back,
        )
        self._skip_back_btn.pack(side="left", padx=2)

        self._play_btn = ctk.CTkButton(
            btn_frame, text="Play", width=70, command=self._on_play_pause,
        )
        self._play_btn.pack(side="left", padx=2)

        self._stop_btn = ctk.CTkButton(
            btn_frame, text="Stop", width=50, command=self._on_stop,
        )
        self._stop_btn.pack(side="left", padx=2)

        self._skip_fwd_btn = ctk.CTkButton(
            btn_frame, text=">>", width=40, command=self._on_skip_forward,
        )
        self._skip_fwd_btn.pack(side="left", padx=2)

        # ── Voice Dropdown ───────────────────────────────────────────

        voice_frame = ctk.CTkFrame(self, fg_color="transparent")
        voice_frame.pack(side="left", padx=(12, 4))

        ctk.CTkLabel(voice_frame, text="Voice:").pack(side="left", padx=(0, 4))

        self._voice_var = ctk.StringVar(value="(loading...)")
        self._voice_map: dict[str, str] = {}  # display name → voice_id

        self._voice_dropdown = ctk.CTkOptionMenu(
            voice_frame,
            variable=self._voice_var,
            values=["(loading...)"],
            width=180,
            command=self._on_voice_changed,
        )
        self._voice_dropdown.pack(side="left")

        # ── Speed Slider ─────────────────────────────────────────────

        speed_frame = ctk.CTkFrame(self, fg_color="transparent")
        speed_frame.pack(side="left", padx=(12, 4))

        self._speed_label = ctk.CTkLabel(speed_frame, text=f"Speed: {DEFAULT_SPEED:.1f}x")
        self._speed_label.pack(side="left", padx=(0, 4))

        self._speed_slider = ctk.CTkSlider(
            speed_frame,
            from_=MIN_SPEED,
            to=MAX_SPEED,
            number_of_steps=30,
            width=120,
            command=self._on_speed_changed,
        )
        self._speed_slider.set(DEFAULT_SPEED)
        self._speed_slider.pack(side="left")

        # ── Volume Slider ────────────────────────────────────────────

        vol_frame = ctk.CTkFrame(self, fg_color="transparent")
        vol_frame.pack(side="left", padx=(12, 8))

        self._volume_label = ctk.CTkLabel(vol_frame, text=f"Vol: {int(DEFAULT_VOLUME * 100)}%")
        self._volume_label.pack(side="left", padx=(0, 4))

        self._volume_slider = ctk.CTkSlider(
            vol_frame,
            from_=0.0,
            to=1.0,
            number_of_steps=20,
            width=100,
            command=self._on_volume_changed,
        )
        self._volume_slider.set(DEFAULT_VOLUME)
        self._volume_slider.pack(side="left")

        # Initially disable playback buttons
        self._set_controls_enabled(False)

    def populate_voices(self, voices: list[VoiceInfo]) -> None:
        """Populate the voice dropdown with available voices."""
        self._voice_map.clear()
        display_names = []
        for v in voices:
            label = f"{v.name} ({v.engine})"
            display_names.append(label)
            self._voice_map[label] = v.voice_id

        if display_names:
            self._voice_dropdown.configure(values=display_names)
            self._voice_var.set(display_names[0])
        else:
            self._voice_dropdown.configure(values=["(no voices)"])
            self._voice_var.set("(no voices)")

    def set_playing_state(self, is_playing: bool, is_paused: bool) -> None:
        """Update button text based on playback state."""
        if is_playing:
            self._play_btn.configure(text="Pause")
        elif is_paused:
            self._play_btn.configure(text="Resume")
        else:
            self._play_btn.configure(text="Play")

    def set_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable playback controls."""
        self._set_controls_enabled(enabled)

    def set_speed(self, speed: float) -> None:
        """Set the speed slider value programmatically."""
        self._speed_slider.set(speed)
        self._speed_label.configure(text=f"Speed: {speed:.1f}x")

    def set_volume(self, volume: float) -> None:
        """Set the volume slider value programmatically."""
        self._volume_slider.set(volume)
        self._volume_label.configure(text=f"Vol: {int(volume * 100)}%")

    # ── Internal ─────────────────────────────────────────────────────

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._play_btn.configure(state=state)
        self._stop_btn.configure(state=state)
        self._skip_back_btn.configure(state=state)
        self._skip_fwd_btn.configure(state=state)

    def _on_play_pause(self) -> None:
        self._app.play_pause()

    def _on_stop(self) -> None:
        self._app.stop()

    def _on_skip_back(self) -> None:
        self._app.skip_back()

    def _on_skip_forward(self) -> None:
        self._app.skip_forward()

    def _on_voice_changed(self, choice: str) -> None:
        voice_id = self._voice_map.get(choice, "")
        if voice_id:
            self._app.set_voice(voice_id)

    def _on_speed_changed(self, value: Any) -> None:
        speed = float(value)
        self._speed_label.configure(text=f"Speed: {speed:.1f}x")
        self._app.set_speed(speed)

    def _on_volume_changed(self, value: Any) -> None:
        volume = float(value)
        self._volume_label.configure(text=f"Vol: {int(volume * 100)}%")
        self._app.set_volume(volume)
