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

## Services

The integration registers these services:

- `lemonade.chat_completion`
- `lemonade.generate_image`
- `lemonade.transcribe_audio`
- `lemonade.text_to_speech`

Service calls support response data. For `text_to_speech`, audio is returned as base64.

## Next planned native Home Assistant platforms

- `conversation` assistant entity
- `ai_task` entity
- `tts` provider
- `stt` provider
- media handling for generated images/audio
