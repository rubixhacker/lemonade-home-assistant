# Speech selection design interview

Status: Product direction confirmed. Implementation and independent verification in progress.

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

Bounded upstream research found no documented saved-voice discovery API. Lemonade's app stores user/assistant reference samples in local app settings, while the speech API accepts a reference sample per request rather than a saved-voice identifier. Therefore automatic discovery of saved OpenMOSS voices is not established. Sources: https://github.com/lemonade-sdk/lemonade/blob/main/src/app/src/renderer/tabs/TTSSettings.tsx and https://github.com/lemonade-sdk/lemonade/blob/main/src/app/src/renderer/utils/appSettings.ts and https://lemonade-server.ai/docs/api/openai/

## Remaining discovery

- Identify or establish the upstream contract for discovering and invoking saved voices, including stable identity, supported languages, and availability. Missing discovery is an upstream dependency, not authorization to move voice lifecycle ownership into Home Assistant.
- Reproduce the reported STT language restriction against the installed provider and version.

The user confirmed this product direction and authorized implementation with Luna subagents and independent Sol verification, submitted as stacked PRs.
