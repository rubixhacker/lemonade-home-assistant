# Graph Report - lemonade-core-quality  (2026-06-19)

## Corpus Check
- 16 files · ~8,704 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 357 nodes · 667 edges · 26 communities (20 shown, 6 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 107 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `02591ea0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]

## God Nodes (most connected - your core abstractions)
1. `LemonadeClient` - 57 edges
2. `LemonadeRuntimeData` - 29 edges
3. `LemonadeCoordinator` - 27 edges
4. `LemonadeError` - 22 edges
5. `LemonadeAuthError` - 21 edges
6. `_get_entry_and_client()` - 18 edges
7. `parse_models_response()` - 17 edges
8. `_async_chat_completion()` - 16 edges
9. `_async_generate_image()` - 14 edges
10. `_async_transcribe_audio()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `FakeConfigEntries` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `Any` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `bool` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `str` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `FakeHass` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py

## Communities (26 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (39): _async_chat_completion(), _async_generate_image(), async_register_services(), _async_text_to_speech(), _async_transcribe_audio(), _default_model(), _extract_chat_content(), _get_entry_and_client() (+31 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (22): bytes, ClientSession, int, headers(), Any, float, str, Return Lemonade Server health. (+14 more)

### Community 2 - "Community 2"
Cohesion: 0.10
Nodes (18): already_configured, config, abort, error, step, api_key, model, name (+10 more)

### Community 3 - "Community 3"
Cohesion: 0.14
Nodes (14): Async client for Lemonade Server's OpenAI-compatible API., Constants for the Lemonade Server integration., Data coordinator for Lemonade Server., The Lemonade Server integration., is_llm(), bool, Model catalog parsing for Lemonade Server., async_create_missing_capability_issue() (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (16): LemonadeCoordinator, Coordinate Lemonade Server health and model catalog updates., LemonadeRuntimeData, LemonadeClient, FakeConfigEntries, FakeEntry, FakeHass, FakeResponse (+8 more)

### Community 5 - "Community 5"
Cohesion: 0.17
Nodes (11): after_dependencies, codeowners, config_flow, dependencies, documentation, domain, integration_type, iot_class (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (35): catalog(), health(), Any, ConfigEntry, HomeAssistant, LemonadeClient, str, Initialize the coordinator. (+27 more)

### Community 7 - "Community 7"
Cohesion: 0.20
Nodes (8): Add from UI, code:text (/config/custom_components/lemonade/), code:text (http://192.168.1.10:13305), code:text (http://localhost:13305), Install, Lemonade Server Home Assistant custom integration, Next planned native Home Assistant platforms, Services

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (17): Architecture, Capability detection, Configure / Options, Data flow, Design decisions, Error handling, Goal, Implementation order (+9 more)

### Community 9 - "Community 9"
Cohesion: 0.22
Nodes (9): code:python (response["data"][0]["b64_json"]), code:python (vol.Optional(ATTR_SAVE, default=False): cv.boolean), code:python (media_dir = hass.config.path("media", "lemonade")), code:python ({"response": response, "media_path": f"media-source://media_), code:text (STT requires a Lemonade model whose labels include stt, tran), code:bash (rtk python3 -m unittest tests.test_models -v), code:bash (rtk graphify update .), code:bash (rtk git add lemonade tests lemonade_custom_component.tar.gz ) (+1 more)

### Community 11 - "Community 11"
Cohesion: 0.25
Nodes (8): code:python (vol.Optional(CONF_API_KEY, description={"suggested_value": e), code:python (@classmethod), code:python (vol.Required(CONF_NAME): str), code:python (vol.Optional(CONF_LLM_HASS_API): SelectSelector(...llm.async), code:json ("entry_not_loaded": "The Lemonade Server entry is not loaded), code:bash (rtk python3 -m py_compile lemonade/*.py), code:bash (rtk git add lemonade/config_flow.py lemonade/strings.json), Task 4: OptionsFlow and profile subentry flows

### Community 12 - "Community 12"
Cohesion: 0.29
Nodes (7): code:json ({), code:python (from homeassistant.const import Platform), code:python (ATTR_SAVE = "save"), code:python (from __future__ import annotations), code:bash (rtk python3 -m py_compile lemonade/*.py), code:bash (rtk git add lemonade/manifest.json lemonade/const.py lemonad), Task 1: Constants, manifest, runtime data skeleton

### Community 13 - "Community 13"
Cohesion: 0.29
Nodes (7): code:python (class LemonadeCoordinator(DataUpdateCoordinator[dict[str, An), code:python ({), code:python (from __future__ import annotations), code:python (client = LemonadeClient(...)), code:bash (rtk python3 -m unittest tests.test_models -v), code:bash (rtk git add lemonade/__init__.py lemonade/api.py lemonade/co), Task 3: Coordinator, runtime setup, and Repairs

### Community 14 - "Community 14"
Cohesion: 0.29
Nodes (7): code:python (_attr_has_entity_name = True), code:python (def __init__(self, entry: LemonadeConfigEntry, key: str) -> ), code:python (server_status: "online" if coordinator.last_update_success e), code:python (self.hass.config_entries.async_update_entry(self.entry, opti), code:bash (rtk python3 -m py_compile lemonade/*.py), code:bash (rtk git add lemonade/entity.py lemonade/sensor.py lemonade/s), Task 5: Entity base, sensors, and selects

### Community 15 - "Community 15"
Cohesion: 0.33
Nodes (6): code:bash (rtk python3 -m unittest tests.test_models -v), code:bash (rtk git add lemonade/models.py tests/test_models.py), code:python (import unittest), code:bash (rtk python3 -m unittest tests.test_models -v), code:python (from __future__ import annotations), Task 2: Model capability parser with tests

### Community 16 - "Community 16"
Cohesion: 0.40
Nodes (4): code:python (_attr_unique_id = subentry.subentry_id), code:bash (rtk python3 -m py_compile lemonade/*.py), code:bash (rtk git add lemonade/llm.py lemonade/conversation.py), Task 6: Shared LLM conversion and Conversation profiles

### Community 17 - "Community 17"
Cohesion: 0.40
Nodes (5): code:python (ai_task.AITaskEntityFeature.GENERATE_DATA | ai_task.AITaskEn), code:python (ai_task.AITaskEntityFeature.GENERATE_IMAGE), code:bash (rtk python3 -m py_compile lemonade/*.py), code:bash (rtk git add lemonade/ai_task.py), Task 7: AI Task profiles

### Community 18 - "Community 18"
Cohesion: 0.40
Nodes (5): code:python (_attr_name = None), code:python (supported_languages = ["en"]), code:bash (rtk python3 -m py_compile lemonade/*.py), code:bash (rtk git add lemonade/tts.py lemonade/stt.py), Task 8: Native TTS and STT providers

### Community 19 - "Community 19"
Cohesion: 0.50
Nodes (3): File structure, Lemonade Home Assistant Core-Quality Implementation Plan, Self-review checklist

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (48): bool, ConfigType, Exception, FlowResult, LemonadeAuthError, LemonadeClient, LemonadeError, Base Lemonade API error. (+40 more)

## Knowledge Gaps
- **98 isolated node(s):** `bool`, `ClientSession`, `int`, `domain`, `name` (+93 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LemonadeClient` connect `Community 25` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 6`?**
  _High betweenness centrality (0.197) - this node is a cross-community bridge._
- **Why does `parse_models_response()` connect `Community 6` to `Community 3`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `LemonadeCoordinator` connect `Community 4` to `Community 25`, `Community 3`, `Community 6`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `LemonadeClient` (e.g. with `FakeConfigEntries` and `Any`) actually correct?**
  _`LemonadeClient` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `LemonadeRuntimeData` (e.g. with `FakeConfigEntries` and `Any`) actually correct?**
  _`LemonadeRuntimeData` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `LemonadeCoordinator` (e.g. with `FakeConfigEntries` and `Any`) actually correct?**
  _`LemonadeCoordinator` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `LemonadeError` (e.g. with `HomeAssistant` and `ConfigType`) actually correct?**
  _`LemonadeError` has 13 INFERRED edges - model-reasoned connections that need verification._