# Speech selection design interview

Status: Kokoro voice selection and model-supported STT implemented. Independent Sol contract and adversarial reviews completed; the legacy British-English finding has a regression fix. OpenMOSS saved-voice selection remains blocked on the upstream public interface.

## Agreed direction

- Use Home Assistant's native TTS language and voice selection experience. Select a language first, then show Speech Voices available for that language, with clear model labels and the native voice preview experience.
- Include Lemonade speech models beyond Kokoro in the design, including OpenMOSS. Offer existing saved voices; creating voices from descriptions and cloning recordings are outside the initial scope.
- Lemonade/OpenMOSS owns the entire saved-voice lifecycle: creation, storage, management, and deletion. Home Assistant discovers and selects those voices; it does not maintain its own reference-sample library. See ADR 0003.
- If a selected voice or its model becomes unavailable, report a clear error requiring another selection. Do not silently substitute another voice or model.
- STT should offer explicit language selection constrained by the selected model's actual support. Automatic language detection is outside the initial scope.
- Separate speech profiles have not been approved or established as necessary.

## Verified facts

Home Assistant supports returning voices for a selected language through `async_get_supported_voices(language)`: https://developers.home-assistant.io/docs/core/entity/tts/

At implementation baseline a8e840a, the integration does not implement that voice list. Both speech entities advertise Home Assistant's entire language registry; STT forwards the selected language unchanged. Upstream main already forwards TTS locales and speaking speed, superseding the older interview checkout. The reported English-only STT picker has not yet been reproduced against the installed system.

Independent Sol review verified OpenMOSS's saved-voice registry (`GET /v1/voices` and saved-ID speech invocation). Lemonade's wrapper does not launch OpenMOSS with `--voice-dir` or expose that registry through its public API. Integration-side saved-voice discovery therefore remains blocked on Lemonade enabling and exposing the backend-owned registry; Home Assistant must not address the private dynamic backend port or store reference samples.

Sources checked at implementation time:
- OpenMOSS registry: https://github.com/pwilkin/openmoss/blob/bfb1f465e0a86fb5a52bbf93e67ceba4b7d0b4e1/src/server/moss_tts_server.cpp#L978-L1098
- Lemonade wrapper: https://github.com/lemonade-sdk/lemonade/blob/788dfb92adfe48e0ff611faf633130270163a568/src/cpp/server/backends/openmoss/openmoss_server.cpp#L181-L224
- Home Assistant filters provider languages against the assistant's main language: https://github.com/home-assistant/core/blob/2026.9.1/homeassistant/components/stt/__init__.py#L425-L462

The English/British-English list is consistent with Home Assistant's native assistant-language filtering. A real Home Assistant WebSocket regression exercises English and French selection; the user's live installation has not been changed.

## Remaining discovery

- Identify or establish the upstream contract for discovering and invoking saved voices, including stable identity, supported languages, and availability. Missing discovery is an upstream dependency, not authorization to move voice lifecycle ownership into Home Assistant.
- Qualify speech output on a live Lemonade server and the user's voice device; automated Home Assistant tests use a controlled HTTP server at the Lemonade boundary.

The user confirmed this product direction and authorized implementation with Luna subagents and independent Sol verification, submitted as stacked PRs.
