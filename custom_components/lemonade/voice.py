"""Compatibility adapters for Lemonade voice generation helpers."""

from __future__ import annotations

from .speech import (
    SpeechSynthesisRequest as VoiceGenerationRequest,
    SpeechSynthesisResult as VoiceGenerationResult,
    audio_extension,
    require_speech_synthesis_model as require_voice_model,
    resolve_speech_synthesis_model as resolve_voice_model,
    speech_synthesis_request as voice_generation_request,
    synthesize_entry_speech as generate_entry_voice,
    synthesize_speech as generate_voice,
)
