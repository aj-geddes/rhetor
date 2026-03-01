"""SettingsDialog — tabbed modal dialog for appearance, voice, and reading settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from constants import (
    DEFAULT_PARAGRAPH_PAUSE_MS,
    DEFAULT_SENTENCE_PAUSE_MS,
)

if TYPE_CHECKING:
    from app import RhetorApp


class SettingsDialog(ctk.CTkToplevel):
    """Modal settings dialog with Appearance, Voice, and Reading tabs."""

    def __init__(self, master: ctk.CTk, app: RhetorApp) -> None:
        super().__init__(master)
        self._app = app
        self._settings_mgr = app.get_settings_manager()
        self._settings = self._settings_mgr.settings

        self.title("Settings")
        self.geometry("500x420")
        self.resizable(False, False)

        # ── Tab View ─────────────────────────────────────────────────

        self._tabview = ctk.CTkTabview(self)
        self._tabview.pack(fill="both", expand=True, padx=12, pady=(12, 4))

        self._tabview.add("Appearance")
        self._tabview.add("Voice")
        self._tabview.add("Reading")

        self._build_appearance_tab()
        self._build_voice_tab()
        self._build_reading_tab()

        # ── Buttons ──────────────────────────────────────────────────

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(4, 12))

        ctk.CTkButton(btn_frame, text="Cancel", width=80, command=self.destroy).pack(
            side="right", padx=4
        )
        ctk.CTkButton(btn_frame, text="Apply", width=80, command=self._on_apply).pack(
            side="right", padx=4
        )

    def _build_appearance_tab(self) -> None:
        tab = self._tabview.tab("Appearance")
        appearance = self._settings.appearance

        # Theme
        ctk.CTkLabel(tab, text="Theme:").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        self._theme_var = ctk.StringVar(value=appearance.theme)
        ctk.CTkOptionMenu(
            tab,
            variable=self._theme_var,
            values=["system", "dark", "light"],
            width=160,
        ).grid(row=0, column=1, sticky="w", padx=8, pady=8)

        # Font size
        ctk.CTkLabel(tab, text="Font Size:").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        self._font_size_var = ctk.IntVar(value=appearance.font_size)
        ctk.CTkSlider(
            tab,
            from_=10,
            to=28,
            number_of_steps=18,
            variable=self._font_size_var,
            width=160,
        ).grid(row=1, column=1, sticky="w", padx=8, pady=8)
        self._font_size_label = ctk.CTkLabel(tab, text=str(appearance.font_size))
        self._font_size_label.grid(row=1, column=2, padx=4, pady=8)
        self._font_size_var.trace_add(
            "write", lambda *a: self._font_size_label.configure(text=str(self._font_size_var.get()))
        )

        # Highlight color
        ctk.CTkLabel(tab, text="Highlight Color:").grid(
            row=2, column=0, sticky="w", padx=8, pady=8
        )
        self._highlight_var = ctk.StringVar(value=appearance.highlight_color)
        ctk.CTkEntry(tab, textvariable=self._highlight_var, width=160).grid(
            row=2, column=1, sticky="w", padx=8, pady=8
        )

    def _build_voice_tab(self) -> None:
        tab = self._tabview.tab("Voice")
        voice = self._settings.voice

        # Preferred engine
        ctk.CTkLabel(tab, text="Preferred Engine:").grid(
            row=0, column=0, sticky="w", padx=8, pady=8
        )
        self._engine_var = ctk.StringVar(value=voice.preferred_engine)
        ctk.CTkOptionMenu(
            tab,
            variable=self._engine_var,
            values=["auto", "edge", "piper", "sapi"],
            width=160,
        ).grid(row=0, column=1, sticky="w", padx=8, pady=8)

        # Force offline
        ctk.CTkLabel(tab, text="Force Offline:").grid(
            row=1, column=0, sticky="w", padx=8, pady=8
        )
        self._offline_var = ctk.BooleanVar(value=voice.force_offline)
        ctk.CTkSwitch(tab, text="", variable=self._offline_var).grid(
            row=1, column=1, sticky="w", padx=8, pady=8
        )

    def _build_reading_tab(self) -> None:
        tab = self._tabview.tab("Reading")
        reading = self._settings.reading

        # Announce headings
        ctk.CTkLabel(tab, text="Announce Headings:").grid(
            row=0, column=0, sticky="w", padx=8, pady=8
        )
        self._announce_var = ctk.BooleanVar(value=reading.announce_headings)
        ctk.CTkSwitch(tab, text="", variable=self._announce_var).grid(
            row=0, column=1, sticky="w", padx=8, pady=8
        )

        # Skip repeated headers
        ctk.CTkLabel(tab, text="Skip Repeated Headers:").grid(
            row=1, column=0, sticky="w", padx=8, pady=8
        )
        self._skip_headers_var = ctk.BooleanVar(value=reading.skip_repeated_headers)
        ctk.CTkSwitch(tab, text="", variable=self._skip_headers_var).grid(
            row=1, column=1, sticky="w", padx=8, pady=8
        )

        # Paragraph pause
        ctk.CTkLabel(tab, text="Paragraph Pause (ms):").grid(
            row=2, column=0, sticky="w", padx=8, pady=8
        )
        self._para_pause_var = ctk.IntVar(value=reading.pause_between_paragraphs_ms)
        ctk.CTkEntry(tab, textvariable=self._para_pause_var, width=80).grid(
            row=2, column=1, sticky="w", padx=8, pady=8
        )

        # Sentence pause
        ctk.CTkLabel(tab, text="Sentence Pause (ms):").grid(
            row=3, column=0, sticky="w", padx=8, pady=8
        )
        self._sent_pause_var = ctk.IntVar(value=reading.pause_between_sentences_ms)
        ctk.CTkEntry(tab, textvariable=self._sent_pause_var, width=80).grid(
            row=3, column=1, sticky="w", padx=8, pady=8
        )

    def _on_apply(self) -> None:
        """Save settings and apply to the application."""
        # Appearance
        self._settings.appearance.theme = self._theme_var.get()
        self._settings.appearance.font_size = self._font_size_var.get()
        self._settings.appearance.highlight_color = self._highlight_var.get()

        # Voice
        self._settings.voice.preferred_engine = self._engine_var.get()
        self._settings.voice.force_offline = self._offline_var.get()

        # Reading
        self._settings.reading.announce_headings = self._announce_var.get()
        self._settings.reading.skip_repeated_headers = self._skip_headers_var.get()

        try:
            self._settings.reading.pause_between_paragraphs_ms = self._para_pause_var.get()
        except (ValueError, TypeError):
            self._settings.reading.pause_between_paragraphs_ms = DEFAULT_PARAGRAPH_PAUSE_MS

        try:
            self._settings.reading.pause_between_sentences_ms = self._sent_pause_var.get()
        except (ValueError, TypeError):
            self._settings.reading.pause_between_sentences_ms = DEFAULT_SENTENCE_PAUSE_MS

        self._app.apply_settings()
        self.destroy()
