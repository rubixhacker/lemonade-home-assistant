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

The proxy must pass through Lemonade's OpenAI-compatible API paths, including `/v1/health`, `/v1/models`, `/v1/chat/completions`, `/v1/images/generations`, `/v1/audio/speech`, `/v1/audio/transcriptions`, and `/v1/classify`. If setup fails, check the Home Assistant log for the exact Lemonade connection or HTTP error.

Leave **Verify SSL certificate** enabled for public CA certificates such as Let's Encrypt. Disable it only for private/self-signed certificates that Home Assistant cannot validate.

Lemonade may need extra time to load a model on its first request. New Server Entries default to a 120-second request timeout. Existing entries keep their saved timeout; increase it under the Server Entry options when image, speech, or larger language models cannot finish a cold start within the previous value. If Lemonade Server itself returns a `model_load_error`, retry once after the model backend finishes starting and check the Lemonade Server logs if it repeats.

## Assist and AI task profiles

The integration creates default model controls for text-to-speech and speech-to-text. Conversation, AI task, and image-capable task models are configured on explicit profiles:

1. Go to **Settings → Devices & services → Lemonade Server**.
2. Set any text-to-speech or speech-to-text default model selectors you want to override.
3. In the entry details, use the **Add service** area or one of the `+` buttons.
4. Choose **Conversation profile** to create an Assist or voice pipeline assistant.
5. Choose **AI task profile** to create an AI suggestions entity.
6. Pick a profile name, model, and optional prompt.
7. For conversation profiles, select any Home Assistant LLM APIs the profile may use when controlling Home Assistant.

Select a Lemonade conversation profile from your Assist pipeline or voice assistant settings. After creating an AI task profile, use Home Assistant AI suggestions, automations, scripts, or service calls that target AI task entities.

### Router Models and Omni Models

When Lemonade Server advertises a downloaded Router Model or Omni Model through
`/v1/models` with the `router` or `omni` recipe, it is available as an explicit
model choice for Conversation Profiles and AI Task Profiles. The selected ID is
sent unchanged to Lemonade Server for Assist, AI task data generation, and
`lemonade.chat_completion`.

These collection models are never selected automatically as a conversation or
AI task fallback. Router policy authoring and Omni component orchestration stay
on Lemonade Server. An older server catalog remains supported; it simply does
not offer collection-model choices. This feature therefore requires a
Lemonade Server release that advertises downloaded collection models, without
raising the integration-wide server requirement.

An Omni response may contain image or audio representations. For chat and AI
task data generation, the integration passes assistant content through its
ordinary chat handling. It does not extract, store, or render those
representations and makes no native media guarantee for them.

## Native Home Assistant platforms

The integration exposes native platforms for:

- Sensors for server status and model counts.
- Select entities for default TTS and STT models.
- Conversation profile subentries for Assist and voice pipelines.
- AI task profile entities with data and image generation support.
- TTS provider support.
- STT provider support.

STT requires a Lemonade model whose labels include stt, transcription, or speech-to-text. The sample model list provided by the user had no STT-capable model, so STT will show unavailable until Lemonade advertises one.

If the voice assistant text-to-speech picker shows both a Lemonade Server entry and an older `lemonade-*` engine, remove the older legacy TTS provider or custom component from Home Assistant. The Lemonade Server integration exposes its current TTS support as the Lemonade Server text-to-speech entity.

## Services

The integration registers these direct services:

- `lemonade.chat_completion`
- `lemonade.generate_image`
- `lemonade.transcribe_audio`
- `lemonade.text_to_speech`
- `lemonade.classify_text`

Direct service model resolution uses the explicit `model` in the service call first, then any configured default model for that capability, then the first compatible model advertised by Lemonade.

Service calls support response data. For `text_to_speech`, audio is returned as base64.

### Text classification

`lemonade.classify_text` requires Lemonade Server v11.5.0 or later. It accepts required `text`, optional Server Entry (`entry_id`), optional Classification Model (`model`), and optional positive `top_k`. The service uses an explicit model first; otherwise it uses the first Classification Model advertised by that Server Entry. It intentionally has no configurable classification default.

The response contains the selected `model` and the complete `labels` score mapping returned by Lemonade Server. Model cards define what those labels mean. Home Assistant does not select a threshold, interpret the labels, or store a classification result.

Older Server Entries remain usable. If no Classification Model is advertised, or the server does not support the classification endpoint, only this service call fails with a classification-specific error.

### Router Models and routing diagnostics

Lemonade Server 11.5.0 or later can expose Router Models through the ordinary chat model selector. `lemonade.chat_completion` accepts optional `route_trace: true` and `router_metadata` inputs. Route decisions remain in the returned raw Lemonade response alongside `content`; Home Assistant does not create a route sensor, event, or history.

Router metadata is an explicit mapping and is passed unchanged. The integration never adds Home Assistant identities, entity context, or profile details. Conversation and AI Task Profiles can store the same optional mapping separately from their prompts.

Lemonade Server owns execution locality. Its mutable routing policy may send request content, Home Assistant tool schemas, and supplied metadata to cloud candidates. Home Assistant does not offer an `allow_cloud` switch or infer a router's locality.

## Generated image media

`lemonade.generate_image` supports `save: true`. When enabled, decoded image bytes from Lemonade image responses are saved under Home Assistant's `/media/lemonade` directory and the service response includes:

```json
{
  "media_path": "media-source://media_source/local/lemonade/<filename>"
}
```

Pass `filename` to choose a filename under `/media/lemonade`; path components are stripped to avoid traversal. If omitted, the default filename uses the decoded image extension, e.g. `lemonade_*.jpg` for JPEG responses and `lemonade_*.png` when no extension is decoded.
