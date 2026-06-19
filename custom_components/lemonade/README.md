# Lemonade Server Home Assistant custom integration

This is an early custom integration for [Lemonade Server](https://lemonade-server.ai/docs/).

## Install

### HACS

Add this repository to HACS as a custom repository with the **Integration** category, install **Lemonade Server**, then restart Home Assistant.

### Manual

Copy this folder to:

```text
/config/custom_components/lemonade/
```

Then restart Home Assistant.

## Add from UI

Go to **Settings → Devices & services → Add integration → Lemonade Server**.

Use a URL like:

```text
http://192.168.1.10:13305
```

or, if Lemonade runs on the same host/container network visible to Home Assistant:

```text
http://localhost:13305
```

For a reverse proxy, use the externally reachable base URL without a trailing slash, for example:

```text
https://lemonade.lan.example
```

The proxy must pass through Lemonade's OpenAI-compatible API paths, including `/v1/health`, `/v1/models`, `/v1/chat/completions`, `/v1/images/generations`, `/v1/audio/speech`, and `/v1/audio/transcriptions`. If setup fails, check the Home Assistant log for the exact Lemonade connection or HTTP error.

Leave **Verify SSL certificate** enabled for public CA certificates such as Let's Encrypt. Disable it only for private/self-signed certificates that Home Assistant cannot validate.

## Assist and AI task profiles

During setup, the integration queries Lemonade and shows **Default model** as a dropdown populated from `/v1/models`. Set **Default model** to use one omni model across Lemonade features, then set any per-capability default only when that feature should use a different model. Conversation agents and AI task entities are added as profiles on the Lemonade integration entry:

1. Go to **Settings → Devices & services → Lemonade Server**.
2. In the entry details, use the **Add service** area or one of the `+` buttons.
3. Choose **Conversation profile** to create an Assist conversation agent.
4. Choose **AI task profile** to create an AI task entity.
5. Pick a profile name, model, and optional prompt.
6. For conversation profiles, select any Home Assistant LLM APIs the profile may use when controlling Home Assistant.

After creating a conversation profile, select it from your Assist pipeline or voice assistant settings as the conversation agent. After creating an AI task profile, use Home Assistant automations, scripts, or service calls that target AI task entities.

## Native Home Assistant platforms

The integration exposes native platforms for:

- Sensors for server status and model counts.
- Select entities for default conversation, AI task, image, TTS, and STT models.
- Conversation agents through conversation profile subentries.
- AI task profile entities with data and image generation support.
- TTS provider support.
- STT provider support.

STT requires a Lemonade model whose labels include stt, transcription, or speech-to-text. The sample model list provided by the user had no STT-capable model, so STT will show unavailable until Lemonade advertises one.

## Services

The integration registers these direct services:

- `lemonade.chat_completion`
- `lemonade.generate_image`
- `lemonade.transcribe_audio`
- `lemonade.text_to_speech`

Direct service model resolution uses the explicit `model` in the service call first, then the configured default model for that capability, then the first compatible model advertised by Lemonade.

Service calls support response data. For `text_to_speech`, audio is returned as base64.

## Generated image media

`lemonade.generate_image` supports `save: true`. When enabled, decoded image bytes from Lemonade image responses are saved under Home Assistant's `/media/lemonade` directory and the service response includes:

```json
{
  "media_path": "media-source://media_source/local/lemonade/<filename>"
}
```

Pass `filename` to choose a filename under `/media/lemonade`; path components are stripped to avoid traversal. If omitted, the default filename uses the decoded image extension, e.g. `lemonade_*.jpg` for JPEG responses and `lemonade_*.png` when no extension is decoded.
