# Lemonade Server Home Assistant Core-Quality Integration Design

Date: 2026-06-18
Target Home Assistant version: 2026.6.3

## Goal

Turn the current Lemonade Server custom integration from a service-only prototype into a Home Assistant core-quality integration that supports visible entities, options, named Assistant/AI Task profiles, native TTS/STT voice pipeline support, direct automation/debug services, image generation/media handling, and Repairs for missing capabilities.

## Design decisions

- The integration targets Home Assistant core-quality structure rather than a quick custom component hack.
- The main config entry represents one Lemonade Server instance.
- Configuration uses a hybrid model strategy: global defaults plus per-capability defaults.
- Conversation and AI Task support multiple named profiles.
- Conversation and AI Task profiles are separate profile types, implemented as config subentries, and inherit global defaults from the main entry.
- Conversation profiles may optionally enable Home Assistant control via HA LLM APIs.
- Image generation returns raw response data and can optionally save images to Home Assistant media storage.
- TTS/STT are available both through native HA voice pipeline platforms and direct services.
- Model capability detection trusts `/v1/models` metadata only. The integration does not run startup probes or guess capabilities.
- Missing capability metadata creates a Home Assistant Repair issue.

## Architecture

The integration is organized around a single server runtime object per config entry. The runtime object owns:

- `LemonadeClient` for async HTTP API calls.
- `LemonadeCoordinator` for polling `/v1/health` and `/v1/models`.
- Parsed model capability data derived from raw `/v1/models` metadata.

The integration forwards the config entry to these platforms:

- `sensor`
- `select`
- `conversation`
- `ai_task`
- `tts`
- `stt`

The main modules are:

- `api.py`: low-level async Lemonade Server API client.
- `models.py`: model metadata parser and capability grouping.
- `coordinator.py`: health/model refresh logic.
- `entity.py`: shared base entity classes.
- `sensor.py`: status and capability count sensors.
- `select.py`: per-capability default model selectors.
- `config_flow.py`: server setup, options flow, and profile subentry flows.
- `conversation.py`: Assist conversation entities for named profiles.
- `ai_task.py`: AI Task entities for named profiles.
- `tts.py`: native Home Assistant TTS provider.
- `stt.py`: native Home Assistant STT provider.
- `repairs.py`: missing capability repair issue helpers.
- `services.py`: direct debug/automation services.

## Data flow

### Startup

1. `async_setup_entry` creates a `LemonadeClient` from config entry data.
2. Startup validates connectivity with `/v1/health`.
3. The integration creates `LemonadeCoordinator`.
4. The coordinator fetches health and model metadata.
5. `models.py` parses raw model metadata into capability groups.
6. Platforms are forwarded.
7. Missing required capabilities create Repair issues.

### Runtime

- Services call `entry.runtime_data.client`.
- Entities read coordinator data through `entry.runtime_data.coordinator`.
- Select entities update config entry options for per-capability defaults.
- Conversation and AI Task entities read their config subentry data and inherit missing settings from main entry defaults.
- TTS/STT providers use their capability-specific default model unless a platform API provides an override.

## Capability detection

Capability detection is metadata-only and uses Lemonade model labels/recipes.

| Capability | Rule |
| --- | --- |
| Conversation / AI Task | `recipe == "llamacpp"` and labels do not include `image`, `tts`, or `embeddings` |
| Home Assistant control capable | labels include `tool-calling` |
| Vision | labels include `vision` |
| Image generation | labels include `image` |
| Image editing | labels include `edit` |
| TTS | labels include `tts` |
| STT | labels include `stt`, `transcription`, or `speech-to-text` |
| Embeddings | labels include `embeddings` |

The integration only lists downloaded models where `downloaded` is true. If the field is absent, the model is treated as available because older Lemonade responses may omit it.

## User-visible behavior

### Integration page

The integration page should show useful entities instead of appearing empty:

- `sensor.lemonade_server_status`
- `sensor.lemonade_model_count`
- `sensor.lemonade_conversation_model_count`
- `sensor.lemonade_image_model_count`
- `sensor.lemonade_tts_model_count`
- `sensor.lemonade_stt_model_count`
- `select.lemonade_default_conversation_model`
- `select.lemonade_default_ai_task_model`
- `select.lemonade_default_image_model`
- `select.lemonade_default_tts_model`
- `select.lemonade_default_stt_model`

Select entities are unavailable when no compatible model is detected for their capability.

### Configure / Options

The integration exposes a Configure flow for:

- request timeout
- API key update/removal
- default conversation model
- default AI Task model
- default image model
- default TTS model
- default STT model

Model dropdowns contain only models detected for the relevant capability.

### Profiles

Conversation and AI Task profiles are named config subentries.

Conversation profile fields:

- name
- model override
- prompt
- enabled Home Assistant LLM APIs

AI Task profile fields:

- name
- model override
- prompt/instructions where supported by the HA `ai_task` API

Profiles inherit global defaults when a field is not set.

### Services

Direct services remain available for testing and automations:

- `lemonade.chat_completion`
- `lemonade.generate_image`
- `lemonade.transcribe_audio`
- `lemonade.text_to_speech`

`lemonade.generate_image` supports raw response return and optional media save. When `save: true`, the service writes generated image bytes to Home Assistant media storage and returns both the raw Lemonade response and saved media path.

## Error handling

- Config flow validates `/v1/health`.
- Startup raises `ConfigEntryAuthFailed` for auth errors.
- Startup raises `ConfigEntryNotReady` for connection, timeout, or temporary server availability errors.
- Startup raises `ConfigEntryError` for incompatible Lemonade responses.
- Coordinator refresh failures mark coordinator data stale/unavailable and log without crashing Home Assistant.
- Missing capability groups create Repairs.
- Entities and native platforms are unavailable when their required capability is missing.
- Services raise clear `HomeAssistantError` messages when no compatible model exists.
- Image media save failures return a clear service failure. Raw response is preserved in logs when safe, but not exposed as success if save was requested and failed.

## Testing strategy

Core-quality tests should cover:

- manifest/config flow loading
- config flow success/failure paths
- client request/response parsing
- `/v1/models` capability parsing using Lemonade sample response shape
- coordinator refresh success/failure
- sensor states and availability
- select options and option updates
- OptionsFlow model dropdown filtering
- Conversation profile subentry creation/update
- AI Task profile subentry creation/update
- missing-capability Repair issue creation
- service schemas and response handling
- native TTS behavior for supported/missing models
- native STT behavior for supported/missing models
- image save-to-media success/failure

## Implementation order

1. Runtime data object, coordinator, and model capability parser.
2. OptionsFlow defaults.
3. Sensor and select entities.
4. Repairs for missing capabilities.
5. Conversation profiles and platform.
6. AI Task profiles and platform.
7. Native TTS/STT providers.
8. Image save-to-media behavior.
9. Test scaffolding and regression tests.

## Non-goals for this implementation pass

- Downloading or installing Lemonade models from Home Assistant.
- Probing capabilities by issuing test inference requests.
- Guessing model support from model names.
- Full embedding platform support.
- Advanced image edit/upscale UI beyond direct services.
