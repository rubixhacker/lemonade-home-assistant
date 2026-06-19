# Graph Report - lemonade-core-quality  (2026-06-19)

## Corpus Check
- 22 files · ~16,050 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 760 nodes · 1517 edges · 51 communities (31 shown, 20 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 247 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3a00c959`
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
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 60|Community 60]]

## God Nodes (most connected - your core abstractions)
1. `LemonadeClient` - 76 edges
2. `RuntimeSetupTest` - 46 edges
3. `LemonadeCoordinator` - 43 edges
4. `LemonadeRuntimeData` - 41 edges
5. `LemonadeProfileSubentryFlow` - 35 edges
6. `LemonadeConfigFlow` - 31 edges
7. `LemonadeOptionsFlow` - 30 edges
8. `Any` - 29 edges
9. `FakeCatalog` - 29 edges
10. `LemonadeError` - 29 edges

## Surprising Connections (you probably didn't know these)
- `str` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `str` --uses--> `LemonadeRuntimeData`  [INFERRED]
  tests/test_runtime.py → lemonade/data.py
- `str` --uses--> `LemonadeProfileSubentryFlow`  [INFERRED]
  tests/test_runtime.py → lemonade/config_flow.py
- `str` --uses--> `LemonadeConfigFlow`  [INFERRED]
  tests/test_runtime.py → lemonade/config_flow.py
- `str` --uses--> `LemonadeOptionsFlow`  [INFERRED]
  tests/test_runtime.py → lemonade/config_flow.py

## Communities (51 total, 20 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (39): _async_chat_completion(), _async_generate_image(), async_register_services(), _async_text_to_speech(), _async_transcribe_audio(), _default_model(), _extract_chat_content(), _get_entry_and_client() (+31 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (27): bytes, ClientSession, int, headers(), Any, bytes, float, int (+19 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (47): LemonadeEntity, LemonadeConfigEntry, str, Base entity for Lemonade Server platforms., Initialize the Lemonade entity., async_setup_entry(), available(), current_option() (+39 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (34): FlowResult, _async_validate_connection(), _entry_current_value(), _model_select_selector(), _profile_type(), Any, str, Config flow for Lemonade Server. (+26 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (91): bool, ConfigSubentryFlow, ConfigType, Exception, LemonadeAuthError, LemonadeClient, LemonadeError, Async client for Lemonade Server's OpenAI-compatible API. (+83 more)

### Community 5 - "Community 5"
Cohesion: 0.17
Nodes (11): after_dependencies, codeowners, config_flow, dependencies, documentation, domain, integration_type, iot_class (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (38): catalog(), health(), Any, ConfigEntry, HomeAssistant, LemonadeClient, str, Initialize the coordinator. (+30 more)

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

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (12): step, title, ai_task_data, conversation, step, title, description, title (+4 more)

### Community 27 - "Community 27"
Cohesion: 0.06
Nodes (70): AssistantContentDeltaDict, _arguments_to_dict(), _arguments_to_json(), _async_add_delta_content_stream(), _async_delta_stream(), async_handle_chat_log(), _attachment_mime_type(), _attachment_to_content_part() (+62 more)

### Community 28 - "Community 28"
Cohesion: 0.12
Nodes (22): async_setup_entry(), _conversation_subentries(), LemonadeConversationEntity, _maybe_await(), AddEntitiesCallback, Any, HomeAssistant, LemonadeConfigEntry (+14 more)

### Community 29 - "Community 29"
Cohesion: 0.07
Nodes (43): _ai_task_subentries(), async_setup_entry(), _catalog_model_ids(), _decode_image_response(), _decode_image_value(), _final_assistant_content(), _first_catalog_model_id(), _image_response_values() (+35 more)

### Community 30 - "Community 30"
Cohesion: 0.15
Nodes (13): name, sensor, name, name, conversation_model_count, image_model_count, model_count, server_status (+5 more)

### Community 46 - "Community 46"
Cohesion: 0.05
Nodes (11): FakeCatalog, FakeConfigEntries, FakeEntry, FakeHass, FakeSession, _profile_flow(), Any, str (+3 more)

### Community 50 - "Community 50"
Cohesion: 0.25
Nodes (7): config, error, step, cannot_connect, invalid_auth, invalid_url, unknown

### Community 51 - "Community 51"
Cohesion: 0.20
Nodes (10): api_key, default_ai_task_model, default_conversation_model, default_image_model, default_stt_model, default_tts_model, data, description (+2 more)

### Community 52 - "Community 52"
Cohesion: 0.48
Nodes (7): already_configured, entry_not_loaded, no_models, unknown_profile_type, abort, abort, abort

### Community 55 - "Community 55"
Cohesion: 0.36
Nodes (8): llm_hass_api, model, name, prompt, timeout, url, data, data

### Community 56 - "Community 56"
Cohesion: 0.25
Nodes (7): config_subentries, issues, missing_capability, description, title, options, step

### Community 60 - "Community 60"
Cohesion: 0.17
Nodes (12): name, name, name, name, name, entity, select, default_ai_task_model (+4 more)

## Knowledge Gaps
- **124 isolated node(s):** `bool`, `HomeAssistant`, `AddEntitiesCallback`, `bool`, `ClientSession` (+119 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LemonadeClient` connect `Community 4` to `Community 0`, `Community 1`, `Community 3`, `Community 6`, `Community 46`?**
  _High betweenness centrality (0.171) - this node is a cross-community bridge._
- **Why does `LemonadeCoordinator` connect `Community 4` to `Community 46`, `Community 2`, `Community 6`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `LemonadeEntity` connect `Community 2` to `Community 4`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 56 inferred relationships involving `LemonadeClient` (e.g. with `_VolMarker` and `str`) actually correct?**
  _`LemonadeClient` has 56 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `RuntimeSetupTest` (e.g. with `LemonadeClient` and `LemonadeRuntimeData`) actually correct?**
  _`RuntimeSetupTest` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `LemonadeCoordinator` (e.g. with `_VolMarker` and `str`) actually correct?**
  _`LemonadeCoordinator` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `LemonadeRuntimeData` (e.g. with `_VolMarker` and `str`) actually correct?**
  _`LemonadeRuntimeData` has 35 INFERRED edges - model-reasoned connections that need verification._