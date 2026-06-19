# Lemonade Server Home Assistant custom integration

This is an early custom integration for [Lemonade Server](https://lemonade-server.ai/docs/).

## Install

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
