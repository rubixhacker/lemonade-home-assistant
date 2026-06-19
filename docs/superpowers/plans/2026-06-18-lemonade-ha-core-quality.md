# Lemonade Home Assistant Core-Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the Lemonade Server custom integration from a service-only config entry into a core-quality Home Assistant integration with options, visible entities, named Conversation/AI Task profiles, native TTS/STT providers, Repairs, and media-aware services.

**Architecture:** Keep `LemonadeClient` as the low-level async API boundary. Add pure model-capability parsing, a coordinator/runtime-data layer, then platform files (`sensor`, `select`, `conversation`, `ai_task`, `tts`, `stt`) that consume runtime data and config subentries. Preserve direct services for debugging and automations.

**Tech Stack:** Home Assistant 2026.6.3 custom integration APIs, `aiohttp`, config entries/subentries, `DataUpdateCoordinator`, HA entity platforms, HA `conversation`, `ai_task`, `tts`, `stt`, Repairs, Python stdlib unit tests for pure parsing.

---

## File structure

- Modify `lemonade/manifest.json`: add `after_dependencies` and `dependencies` entries for Assist, AI Task, TTS, and STT exactly as shown in Task 1.
- Modify `lemonade/const.py`: add platform list, option keys, capability constants, subentry types, sensor/select metadata constants, media service attributes.
- Modify `lemonade/api.py`: keep existing client; add optional `tools`, `response_format`, image decode helpers, and robust `/v1/models` normalization.
- Create `lemonade/models.py`: pure model metadata parser and capability grouping. No Home Assistant imports.
- Create `tests/test_models.py`: stdlib tests for `models.py` using a compact version of the user-provided `/v1/models` response.
- Create `lemonade/coordinator.py`: `LemonadeCoordinator` that fetches health/models and stores parsed capabilities.
- Create `lemonade/data.py`: `LemonadeConfigEntry` type alias and `LemonadeRuntimeData` dataclass.
- Create `lemonade/repairs.py`: helper to create/delete missing capability repair issues.
- Create `lemonade/entity.py`: base entity with device info and coordinator access.
- Create `lemonade/sensor.py`: server status/model count/capability count sensors.
- Create `lemonade/select.py`: default model selectors per capability.
- Modify `lemonade/config_flow.py`: add OptionsFlow and config subentry flows for Conversation and AI Task profiles.
- Create `lemonade/llm.py`: shared conversion between HA conversation chat logs/tools and OpenAI-compatible Lemonade chat-completion payloads.
- Create `lemonade/conversation.py`: native Assist conversation entities per Conversation profile.
- Create `lemonade/ai_task.py`: native AI Task entities per AI Task profile.
- Create `lemonade/tts.py`: native `TextToSpeechEntity` provider.
- Create `lemonade/stt.py`: native `SpeechToTextEntity` provider.
- Modify `lemonade/services.py`: use runtime/coordinator model selection, add `save`/media handling for image generation, keep response data.
- Modify `lemonade/services.yaml`: document new service fields.
- Modify `lemonade/strings.json`: add options, subentries, entity names, errors, repairs.
- Modify `lemonade/README.md`: document install, platforms, profiles, services, and known STT metadata requirement.

---

### Task 1: Constants, manifest, runtime data skeleton

**Files:**
- Modify: `lemonade/manifest.json`
- Modify: `lemonade/const.py`
- Create: `lemonade/data.py`

- [ ] **Step 1: Update manifest metadata**

Replace `lemonade/manifest.json` with:

```json
{
  "domain": "lemonade",
  "name": "Lemonade Server",
  "version": "0.2.0",
  "after_dependencies": ["assist_pipeline", "intent"],
  "codeowners": [],
  "config_flow": true,
  "dependencies": ["ai_task", "conversation", "stt", "tts"],
  "documentation": "https://lemonade-server.ai/docs/",
  "integration_type": "service",
  "iot_class": "local_polling",
  "requirements": []
}
```

- [ ] **Step 2: Replace constants with core-quality names**

Replace `lemonade/const.py` with constants for platform forwarding and per-capability options. The required keys are:

```python
from homeassistant.const import Platform

DOMAIN = "lemonade"
DEFAULT_NAME = "Lemonade Server"
DEFAULT_URL = "http://localhost:13305"
DEFAULT_TIMEOUT = 30.0
DEFAULT_SCAN_INTERVAL_SECONDS = 60

CONF_TIMEOUT = "timeout"
CONF_ENTRY_ID = "entry_id"
CONF_DEFAULT_CONVERSATION_MODEL = "default_conversation_model"
CONF_DEFAULT_AI_TASK_MODEL = "default_ai_task_model"
CONF_DEFAULT_IMAGE_MODEL = "default_image_model"
CONF_DEFAULT_TTS_MODEL = "default_tts_model"
CONF_DEFAULT_STT_MODEL = "default_stt_model"
CONF_LLM_HASS_API = "llm_hass_api"

SUBENTRY_TYPE_CONVERSATION = "conversation"
SUBENTRY_TYPE_AI_TASK = "ai_task_data"

CAPABILITY_CONVERSATION = "conversation"
CAPABILITY_AI_TASK = "ai_task"
CAPABILITY_TOOL_CALLING = "tool_calling"
CAPABILITY_VISION = "vision"
CAPABILITY_IMAGE = "image"
CAPABILITY_IMAGE_EDIT = "image_edit"
CAPABILITY_TTS = "tts"
CAPABILITY_STT = "stt"
CAPABILITY_EMBEDDINGS = "embeddings"
CAPABILITIES = (
    CAPABILITY_CONVERSATION,
    CAPABILITY_AI_TASK,
    CAPABILITY_TOOL_CALLING,
    CAPABILITY_VISION,
    CAPABILITY_IMAGE,
    CAPABILITY_IMAGE_EDIT,
    CAPABILITY_TTS,
    CAPABILITY_STT,
    CAPABILITY_EMBEDDINGS,
)
MODEL_OPTION_BY_CAPABILITY = {
    CAPABILITY_CONVERSATION: CONF_DEFAULT_CONVERSATION_MODEL,
    CAPABILITY_AI_TASK: CONF_DEFAULT_AI_TASK_MODEL,
    CAPABILITY_IMAGE: CONF_DEFAULT_IMAGE_MODEL,
    CAPABILITY_TTS: CONF_DEFAULT_TTS_MODEL,
    CAPABILITY_STT: CONF_DEFAULT_STT_MODEL,
}
PLATFORMS = (
    Platform.SENSOR,
    Platform.SELECT,
    Platform.CONVERSATION,
    Platform.AI_TASK,
    Platform.TTS,
    Platform.STT,
)
```

Keep existing service names and endpoint constants, and add:

```python
ATTR_SAVE = "save"
ATTR_FILENAME = "filename"
ATTR_MEDIA_PATH = "media_path"
ATTR_ATTACHMENTS = "attachments"
ATTR_STRUCTURE = "structure"
```

- [ ] **Step 3: Create runtime-data dataclass**

Create `lemonade/data.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

from .api import LemonadeClient

if TYPE_CHECKING:
    from .coordinator import LemonadeCoordinator


@dataclass
class LemonadeRuntimeData:
    client: LemonadeClient
    coordinator: LemonadeCoordinator


type LemonadeConfigEntry = ConfigEntry[LemonadeRuntimeData]
```

- [ ] **Step 4: Verify syntax**

Run:

```bash
rtk python3 -m py_compile lemonade/*.py
rtk python3 -m json.tool lemonade/manifest.json >/tmp/lemonade-manifest.json
```

Expected: command exits 0.

- [ ] **Step 5: Commit**

```bash
rtk git add lemonade/manifest.json lemonade/const.py lemonade/data.py
rtk git commit -m "feat: add Lemonade runtime constants"
```

---

### Task 2: Model capability parser with tests

**Files:**
- Create: `lemonade/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing parser tests**

Create `tests/test_models.py`:

```python
import unittest

from lemonade.const import (
    CAPABILITY_AI_TASK,
    CAPABILITY_CONVERSATION,
    CAPABILITY_EMBEDDINGS,
    CAPABILITY_IMAGE,
    CAPABILITY_IMAGE_EDIT,
    CAPABILITY_STT,
    CAPABILITY_TOOL_CALLING,
    CAPABILITY_TTS,
    CAPABILITY_VISION,
)
from lemonade.models import parse_models_response


SAMPLE = {
    "data": [
        {
            "id": "Bonsai-8B-gguf",
            "downloaded": True,
            "labels": ["llamacpp", "tool-calling"],
            "recipe": "llamacpp",
            "max_context_window": 65536,
        },
        {
            "id": "Flux-2-Klein-9B-GGUF",
            "downloaded": True,
            "labels": ["image", "edit"],
            "recipe": "sd-cpp",
            "image_defaults": {"width": 256, "height": 256, "steps": 4},
        },
        {
            "id": "Qwen3.6-27B-GGUF",
            "downloaded": True,
            "labels": ["vision", "tool-calling"],
            "recipe": "llamacpp",
        },
        {
            "id": "kokoro-v1",
            "downloaded": True,
            "labels": ["tts"],
            "recipe": "kokoro",
        },
        {
            "id": "Qwen3-Embedding-0.6B-GGUF",
            "downloaded": True,
            "labels": ["embeddings"],
            "recipe": "llamacpp",
        },
        {
            "id": "future-stt",
            "downloaded": True,
            "labels": ["speech-to-text"],
            "recipe": "moonshine",
        },
        {
            "id": "not-downloaded",
            "downloaded": False,
            "labels": ["tool-calling"],
            "recipe": "llamacpp",
        },
    ]
}


class ParseModelsResponseTest(unittest.TestCase):
    def test_groups_models_by_metadata_only_capabilities(self):
        catalog = parse_models_response(SAMPLE)

        self.assertEqual(catalog.model_ids(CAPABILITY_CONVERSATION), ["Bonsai-8B-gguf", "Qwen3.6-27B-GGUF"])
        self.assertEqual(catalog.model_ids(CAPABILITY_AI_TASK), ["Bonsai-8B-gguf", "Qwen3.6-27B-GGUF"])
        self.assertEqual(catalog.model_ids(CAPABILITY_TOOL_CALLING), ["Bonsai-8B-gguf", "Qwen3.6-27B-GGUF"])
        self.assertEqual(catalog.model_ids(CAPABILITY_VISION), ["Qwen3.6-27B-GGUF"])
        self.assertEqual(catalog.model_ids(CAPABILITY_IMAGE), ["Flux-2-Klein-9B-GGUF"])
        self.assertEqual(catalog.model_ids(CAPABILITY_IMAGE_EDIT), ["Flux-2-Klein-9B-GGUF"])
        self.assertEqual(catalog.model_ids(CAPABILITY_TTS), ["kokoro-v1"])
        self.assertEqual(catalog.model_ids(CAPABILITY_STT), ["future-stt"])
        self.assertEqual(catalog.model_ids(CAPABILITY_EMBEDDINGS), ["Qwen3-Embedding-0.6B-GGUF"])

    def test_ignores_not_downloaded_models(self):
        catalog = parse_models_response(SAMPLE)

        self.assertNotIn("not-downloaded", catalog.all_model_ids)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
rtk python3 -m unittest tests.test_models -v
```

Expected: FAIL because `lemonade.models` does not exist.

- [ ] **Step 3: Implement parser**

Create `lemonade/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import (
    CAPABILITIES,
    CAPABILITY_AI_TASK,
    CAPABILITY_CONVERSATION,
    CAPABILITY_EMBEDDINGS,
    CAPABILITY_IMAGE,
    CAPABILITY_IMAGE_EDIT,
    CAPABILITY_STT,
    CAPABILITY_TOOL_CALLING,
    CAPABILITY_TTS,
    CAPABILITY_VISION,
)

EXCLUDED_LLM_LABELS = {"image", "tts", "embeddings"}
STT_LABELS = {"stt", "transcription", "speech-to-text"}


@dataclass(frozen=True)
class LemonadeModel:
    id: str
    labels: frozenset[str]
    recipe: str | None
    downloaded: bool
    raw: dict[str, Any]

    @property
    def is_llm(self) -> bool:
        return self.recipe == "llamacpp" and not self.labels.intersection(EXCLUDED_LLM_LABELS)


@dataclass(frozen=True)
class LemonadeModelCatalog:
    models: tuple[LemonadeModel, ...]
    by_capability: dict[str, tuple[LemonadeModel, ...]] = field(default_factory=dict)

    @property
    def all_model_ids(self) -> list[str]:
        return [model.id for model in self.models]

    def models_for(self, capability: str) -> tuple[LemonadeModel, ...]:
        return self.by_capability.get(capability, ())

    def model_ids(self, capability: str) -> list[str]:
        return [model.id for model in self.models_for(capability)]

    def first_model_id(self, capability: str) -> str | None:
        models = self.models_for(capability)
        return models[0].id if models else None


def _raw_models(response: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(response, list):
        return [item for item in response if isinstance(item, dict)]
    data = response.get("data") or response.get("models") or []
    return [item for item in data if isinstance(item, dict)]


def _capabilities(model: LemonadeModel) -> set[str]:
    labels = model.labels
    capabilities: set[str] = set()
    if model.is_llm:
        capabilities.add(CAPABILITY_CONVERSATION)
        capabilities.add(CAPABILITY_AI_TASK)
    if "tool-calling" in labels:
        capabilities.add(CAPABILITY_TOOL_CALLING)
    if "vision" in labels:
        capabilities.add(CAPABILITY_VISION)
    if "image" in labels:
        capabilities.add(CAPABILITY_IMAGE)
    if "edit" in labels:
        capabilities.add(CAPABILITY_IMAGE_EDIT)
    if "tts" in labels:
        capabilities.add(CAPABILITY_TTS)
    if labels.intersection(STT_LABELS):
        capabilities.add(CAPABILITY_STT)
    if "embeddings" in labels:
        capabilities.add(CAPABILITY_EMBEDDINGS)
    return capabilities


def parse_models_response(response: dict[str, Any] | list[dict[str, Any]]) -> LemonadeModelCatalog:
    parsed: list[LemonadeModel] = []
    grouped: dict[str, list[LemonadeModel]] = {capability: [] for capability in CAPABILITIES}

    for raw in _raw_models(response):
        model_id = raw.get("id")
        if not isinstance(model_id, str) or not model_id:
            continue
        downloaded = bool(raw.get("downloaded", True))
        if not downloaded:
            continue
        labels = frozenset(str(label) for label in raw.get("labels", []) if isinstance(label, str))
        recipe = raw.get("recipe") if isinstance(raw.get("recipe"), str) else None
        model = LemonadeModel(model_id, labels, recipe, downloaded, raw)
        parsed.append(model)
        for capability in _capabilities(model):
            grouped[capability].append(model)

    return LemonadeModelCatalog(
        models=tuple(parsed),
        by_capability={capability: tuple(models) for capability, models in grouped.items()},
    )
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
rtk python3 -m unittest tests.test_models -v
rtk python3 -m py_compile lemonade/*.py
```

Expected: tests pass and py_compile exits 0.

- [ ] **Step 5: Commit**

```bash
rtk git add lemonade/models.py tests/test_models.py
rtk git commit -m "feat: parse Lemonade model capabilities"
```

---

### Task 3: Coordinator, runtime setup, and Repairs

**Files:**
- Create: `lemonade/coordinator.py`
- Create: `lemonade/repairs.py`
- Modify: `lemonade/__init__.py`
- Modify: `lemonade/api.py`

- [ ] **Step 1: Create coordinator**

Create `lemonade/coordinator.py` with `LemonadeCoordinator(DataUpdateCoordinator)` that fetches `client.health()` and `client.models()`, parses models with `parse_models_response`, and exposes `health`, `catalog`, and `server_status` properties.

Required constructor signature:

```python
class LemonadeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: LemonadeClient) -> None:
```

Required `_async_update_data` result shape:

```python
{
    "health": health,
    "models": raw_models,
    "catalog": parse_models_response(raw_models),
}
```

Use `timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS)` for `update_interval`.

- [ ] **Step 2: Add Repairs helper**

Create `lemonade/repairs.py`:

```python
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN


def async_create_missing_capability_issue(hass: HomeAssistant, entry_id: str, capability: str) -> None:
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"missing_{capability}_{entry_id}",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="missing_capability",
        translation_placeholders={"capability": capability},
    )


def async_delete_missing_capability_issue(hass: HomeAssistant, entry_id: str, capability: str) -> None:
    ir.async_delete_issue(hass, DOMAIN, f"missing_{capability}_{entry_id}")
```

- [ ] **Step 3: Wire runtime data in `__init__.py`**

Modify `async_setup_entry` to:

```python
client = LemonadeClient(...)
await client.health()
coordinator = LemonadeCoordinator(hass, entry, client)
await coordinator.async_config_entry_first_refresh()
entry.runtime_data = LemonadeRuntimeData(client=client, coordinator=coordinator)
await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
```

Also call a helper that creates/deletes Repair issues for `image`, `tts`, and `stt` capabilities based on `coordinator.catalog.model_ids(capability)`.

- [ ] **Step 4: Normalize `/v1/models` in API client**

Modify `LemonadeClient.models()` to return the raw dict from `/v1/models`. Do not coerce to `{"models": ...}`; `models.py` handles both `data` and `models` forms.

- [ ] **Step 5: Verify**

Run:

```bash
rtk python3 -m unittest tests.test_models -v
rtk python3 -m py_compile lemonade/*.py
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
rtk git add lemonade/__init__.py lemonade/api.py lemonade/coordinator.py lemonade/repairs.py
rtk git commit -m "feat: add Lemonade coordinator runtime"
```

---

### Task 4: OptionsFlow and profile subentry flows

**Files:**
- Modify: `lemonade/config_flow.py`
- Modify: `lemonade/strings.json`

- [ ] **Step 1: Add OptionsFlow skeleton**

Add `@staticmethod async_get_options_flow(config_entry)` to `LemonadeConfigFlow` returning `LemonadeOptionsFlow(config_entry)`.

Implement `LemonadeOptionsFlow(config_entries.OptionsFlow)` with `async_step_init`. It should show fields:

```python
vol.Optional(CONF_API_KEY, description={"suggested_value": existing_api_key_or_empty}): str
vol.Required(CONF_TIMEOUT, default=current_timeout): vol.Coerce(float)
vol.Optional(CONF_DEFAULT_CONVERSATION_MODEL, default=current): SelectSelector(...conversation models...)
vol.Optional(CONF_DEFAULT_AI_TASK_MODEL, default=current): SelectSelector(...ai_task models...)
vol.Optional(CONF_DEFAULT_IMAGE_MODEL, default=current): SelectSelector(...image models...)
vol.Optional(CONF_DEFAULT_TTS_MODEL, default=current): SelectSelector(...tts models...)
vol.Optional(CONF_DEFAULT_STT_MODEL, default=current): SelectSelector(...stt models...)
```

Use the loaded entry's `runtime_data.coordinator.catalog` to populate each dropdown. If a capability has no models, omit that selector.

- [ ] **Step 2: Persist options**

On submit, call `self.async_create_entry(title="", data=user_input)` and rely on `async_update_options` to reload.

- [ ] **Step 3: Add subentry flow registration**

Add:

```python
@classmethod
@callback
def async_get_supported_subentry_types(cls, config_entry: ConfigEntry) -> dict[str, type[ConfigSubentryFlow]]:
    return {
        SUBENTRY_TYPE_CONVERSATION: LemonadeProfileSubentryFlow,
        SUBENTRY_TYPE_AI_TASK: LemonadeProfileSubentryFlow,
    }
```

- [ ] **Step 4: Implement `LemonadeProfileSubentryFlow`**

Fields for new subentry:

```python
vol.Required(CONF_NAME): str
vol.Optional(CONF_MODEL): SelectSelector(...capability models...)
vol.Optional(CONF_PROMPT): TemplateSelector()
```

For conversation subentries only, include:

```python
vol.Optional(CONF_LLM_HASS_API): SelectSelector(...llm.async_get_apis(hass), multiple=True...)
```

Use subentry type to select model list: conversation uses `CAPABILITY_CONVERSATION`, AI Task uses `CAPABILITY_AI_TASK`.

- [ ] **Step 5: Update strings**

Add strings for options and subentry creation. Include errors:

```json
"entry_not_loaded": "The Lemonade Server entry is not loaded.",
"no_models": "No compatible Lemonade models are available for this profile type."
```

- [ ] **Step 6: Verify**

Run:

```bash
rtk python3 -m py_compile lemonade/*.py
rtk python3 -m json.tool lemonade/strings.json >/tmp/lemonade-strings.json
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
rtk git add lemonade/config_flow.py lemonade/strings.json
rtk git commit -m "feat: add Lemonade options and profiles"
```

---

### Task 5: Entity base, sensors, and selects

**Files:**
- Create: `lemonade/entity.py`
- Create: `lemonade/sensor.py`
- Create: `lemonade/select.py`
- Modify: `lemonade/strings.json`

- [ ] **Step 1: Create base entity**

Create `LemonadeEntity(CoordinatorEntity[LemonadeCoordinator])` with:

```python
_attr_has_entity_name = True
_attr_device_info = DeviceInfo(
    identifiers={(DOMAIN, entry.entry_id)},
    name=entry.title,
    manufacturer="Lemonade Server",
    entry_type=DeviceEntryType.SERVICE,
)
```

Constructor:

```python
def __init__(self, entry: LemonadeConfigEntry, key: str) -> None:
    super().__init__(entry.runtime_data.coordinator)
    self.entry = entry
    self._attr_unique_id = f"{entry.entry_id}_{key}"
```

- [ ] **Step 2: Add sensors**

Create `sensor.py` with `async_setup_entry` adding:

- `LemonadeServerStatusSensor`
- `LemonadeTotalModelCountSensor`
- one `LemonadeCapabilityCountSensor` for each of conversation, image, tts, stt

Sensor states:

```python
server_status: "online" if coordinator.last_update_success else "offline"
total count: len(coordinator.catalog.models)
capability count: len(coordinator.catalog.models_for(capability))
```

- [ ] **Step 3: Add selects**

Create `select.py` with one `SelectEntity` per default capability option. Options come from `coordinator.catalog.model_ids(capability)`. On select, update entry options:

```python
self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, option_key: option})
await self.hass.config_entries.async_reload(self.entry.entry_id)
```

The select is unavailable when its options list is empty.

- [ ] **Step 4: Update strings**

Add entity translation keys for server status, model count, conversation model count, image model count, tts model count, stt model count, and default model selects.

- [ ] **Step 5: Verify**

Run:

```bash
rtk python3 -m py_compile lemonade/*.py
rtk python3 -m json.tool lemonade/strings.json >/tmp/lemonade-strings.json
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
rtk git add lemonade/entity.py lemonade/sensor.py lemonade/select.py lemonade/strings.json
rtk git commit -m "feat: add Lemonade status entities"
```

---

### Task 6: Shared LLM conversion and Conversation profiles

**Files:**
- Create: `lemonade/llm.py`
- Create: `lemonade/conversation.py`

- [ ] **Step 1: Create LLM conversion helpers**

Create `llm.py` with:

- `format_tool(tool, custom_serializer)` producing OpenAI-compatible `{"type":"function","function":...}` specs using `voluptuous_openapi.convert`.
- `content_to_message(content)` converting HA `SystemContent`, `UserContent`, `AssistantContent`, and `ToolResultContent` to OpenAI-compatible messages.
- `response_to_delta(response)` yielding one HA `AssistantContentDeltaDict` from non-streaming chat response.
- `async_handle_chat_log(entity_id, client, model, chat_log, structure=None)` that loops up to `MAX_TOOL_ITERATIONS = 10`, calls `client.chat_completion(...)`, adds deltas to `chat_log.async_add_delta_content_stream`, and stops when `chat_log.unresponded_tool_results` is empty.

For tool calls, parse response choices message `tool_calls` into `llm.ToolInput` deltas.

- [ ] **Step 2: Add conversation entity**

Create `conversation.py` with `LemonadeConversationEntity(conversation.ConversationEntity, conversation.AbstractConversationAgent, Entity)`.

Constructor receives `LemonadeConfigEntry` and `ConfigSubentry`. Set:

```python
_attr_unique_id = subentry.subentry_id
_attr_name = None
_attr_has_entity_name = True
_attr_supported_features = conversation.ConversationEntityFeature.CONTROL if subentry.data.get(CONF_LLM_HASS_API) else 0
```

`async_setup_entry` adds one entity for each subentry with `subentry_type == "conversation"`.

- [ ] **Step 3: Implement message handling**

In `_async_handle_message`, call:

```python
await chat_log.async_provide_llm_data(
    user_input.as_llm_context(DOMAIN),
    self.subentry.data.get(CONF_LLM_HASS_API),
    self.subentry.data.get(CONF_PROMPT),
    user_input.extra_system_prompt,
)
await async_handle_chat_log(self.entity_id, self.entry.runtime_data.client, model, chat_log)
return conversation.async_get_result_from_chat_log(user_input, chat_log)
```

Model resolution: subentry model, then default conversation option, then first conversation model from catalog. If none, raise `HomeAssistantError("No Lemonade conversation model is available")`.

- [ ] **Step 4: Verify**

Run:

```bash
rtk python3 -m py_compile lemonade/*.py
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
rtk git add lemonade/llm.py lemonade/conversation.py
rtk git commit -m "feat: add Lemonade conversation profiles"
```

---

### Task 7: AI Task profiles

**Files:**
- Create: `lemonade/ai_task.py`

- [ ] **Step 1: Add AI Task entity**

Create `ai_task.py` with `LemonadeAITaskEntity(ai_task.AITaskEntity, Entity)`.

Set supported features:

```python
ai_task.AITaskEntityFeature.GENERATE_DATA | ai_task.AITaskEntityFeature.SUPPORT_ATTACHMENTS
```

If image models exist, also set:

```python
ai_task.AITaskEntityFeature.GENERATE_IMAGE
```

- [ ] **Step 2: Implement data generation**

In `_async_generate_data`, call shared `async_handle_chat_log(...)` with model resolved from subentry/default AI task/first AI task model. If `task.structure` is present, request structured output if possible; at minimum instruct the model to return JSON and parse `chat_log.content[-1].content` with `json_loads`. Return `ai_task.GenDataTaskResult(conversation_id=chat_log.conversation_id, data=parsed_or_text)`.

- [ ] **Step 3: Implement image generation**

In `_async_generate_image`, resolve image model, call `client.generate_image(prompt=task.instructions, model=image_model)`, decode the first image from either `b64_json`, `url`, or Lemonade raw response with image data. Return `ai_task.GenImageTaskResult(image_data=image_bytes, conversation_id=chat_log.conversation_id, mime_type="image/png", model=image_model)`.

- [ ] **Step 4: Verify**

Run:

```bash
rtk python3 -m py_compile lemonade/*.py
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
rtk git add lemonade/ai_task.py
rtk git commit -m "feat: add Lemonade AI task profiles"
```

---

### Task 8: Native TTS and STT providers

**Files:**
- Create: `lemonade/tts.py`
- Create: `lemonade/stt.py`

- [ ] **Step 1: Add TTS entity**

Create `tts.py` with `LemonadeTTSEntity(TextToSpeechEntity)`. Set:

```python
_attr_name = None
_attr_has_entity_name = True
_attr_unique_id = f"{entry.entry_id}_tts"
_attr_default_language = "en"
_attr_supported_languages = ["en"]
_attr_supported_options = ["voice", "model", "response_format"]
```

Implement `async_get_tts_audio(message, language, options)` to resolve model from `options["model"]`, default TTS option, or first TTS model. Call `client.text_to_speech(...)`, derive extension from content type/response_format, and return `(extension, audio_bytes)`.

- [ ] **Step 2: Add STT entity**

Create `stt.py` with `LemonadeSTTEntity(stt.SpeechToTextEntity)`. Set supported metadata:

```python
supported_languages = ["en"]
supported_formats = [stt.AudioFormats.WAV]
supported_codecs = [stt.AudioCodecs.PCM]
supported_bit_rates = [stt.AudioBitRates.BITRATE_16]
supported_sample_rates = [stt.AudioSampleRates.SAMPLERATE_16000]
supported_channels = [stt.AudioChannels.CHANNEL_MONO]
```

Implement `async_process_audio_stream` to collect stream bytes, resolve model from default STT option or first STT model, call `client.transcribe_audio(...)`, and return `stt.SpeechResult(text, stt.SpeechResultState.SUCCESS)`. On error, return `SpeechResult(None, SpeechResultState.ERROR)` and log exception.

- [ ] **Step 3: Make missing STT explicit**

If no STT model exists, still create the STT entity but set available false. This lets Repairs explain why it is unavailable.

- [ ] **Step 4: Verify**

Run:

```bash
rtk python3 -m py_compile lemonade/*.py
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
rtk git add lemonade/tts.py lemonade/stt.py
rtk git commit -m "feat: add Lemonade voice providers"
```

---

### Task 9: Media-aware services and final docs

**Files:**
- Modify: `lemonade/services.py`
- Modify: `lemonade/services.yaml`
- Modify: `lemonade/README.md`
- Modify: `lemonade/strings.json`

- [ ] **Step 1: Add image decode helper**

In `services.py`, add `extract_image_bytes(response)` that checks, in order:

```python
response["data"][0]["b64_json"]
response["data"][0]["url"] if it is a data:image/...;base64 URL
response["b64_json"]
response["image"]
```

Return `(image_bytes, extension)` or `(None, None)`.

- [ ] **Step 2: Add media save fields**

Extend `GENERATE_IMAGE_SCHEMA` with:

```python
vol.Optional(ATTR_SAVE, default=False): cv.boolean
vol.Optional(ATTR_FILENAME): cv.string
```

- [ ] **Step 3: Save generated images when requested**

When `save` is true, write bytes to:

```python
media_dir = hass.config.path("media", "lemonade")
filename = call.data.get(ATTR_FILENAME) or f"lemonade_{utcnow_slug}.png"
path = Path(media_dir) / filename
```

Use `hass.async_add_executor_job` for directory creation and writing. Return:

```python
{"response": response, "media_path": f"media-source://media_source/local/lemonade/{filename}"}
```

If no image bytes are found, raise `HomeAssistantError("Lemonade image response did not contain image bytes to save")`.

- [ ] **Step 4: Use coordinator defaults in all services**

Update service model resolution to prefer explicit service model, then capability default option, then first model in that capability group. Use conversation capability for chat, image capability for generate image, TTS capability for text-to-speech, STT capability for transcription.

- [ ] **Step 5: Update service docs**

Update `services.yaml` to include `save`, `filename`, and model-resolution descriptions.

Update `README.md` to include:

```text
STT requires a Lemonade model whose labels include stt, transcription, or speech-to-text. The sample model list provided by the user had no STT-capable model, so STT will show unavailable until Lemonade advertises one.
```

- [ ] **Step 6: Final verification**

Run:

```bash
rtk python3 -m unittest tests.test_models -v
rtk python3 -m py_compile lemonade/*.py
rtk python3 -m json.tool lemonade/manifest.json >/tmp/lemonade-manifest.json
rtk python3 -m json.tool lemonade/strings.json >/tmp/lemonade-strings.json
rtk rm -rf lemonade/__pycache__ lemonade_custom_component.tar.gz
rtk tar -czf lemonade_custom_component.tar.gz lemonade
rtk tar -tzf lemonade_custom_component.tar.gz
```

Expected: tests pass, syntax passes, JSON validates, tarball contains no `__pycache__`.

- [ ] **Step 7: Update graph**

Run:

```bash
rtk graphify update .
```

Expected: graph updates successfully.

- [ ] **Step 8: Commit**

```bash
rtk git add lemonade tests lemonade_custom_component.tar.gz graphify-out
rtk git commit -m "feat: complete Lemonade core-quality integration"
```

---

## Self-review checklist

- Spec coverage: Tasks cover runtime/coordinator, OptionsFlow, entities, Repairs, Conversation profiles, AI Task profiles, native TTS/STT, image media save, direct services, and docs.
- Placeholder scan: No forbidden placeholder markers or vague unassigned tasks remain.
- Type consistency: Runtime data is `LemonadeRuntimeData`; config entries use `LemonadeConfigEntry`; model capability parser exposes `model_ids`, `models_for`, and `first_model_id`; platforms read through `entry.runtime_data.coordinator`.
- Known limitation: Full HA integration tests are planned structurally, but local execution will verify pure parser tests, syntax, JSON validity, tarball cleanliness, and Home Assistant startup logs after user copy.
