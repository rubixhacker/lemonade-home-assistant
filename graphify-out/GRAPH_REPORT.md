# Graph Report - lemonade-core-quality  (2026-06-19)

## Corpus Check
- 16 files · ~10,709 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 493 nodes · 1032 edges · 41 communities (31 shown, 10 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 221 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `45b8f3c9`
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
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]

## God Nodes (most connected - your core abstractions)
1. `LemonadeClient` - 75 edges
2. `LemonadeRuntimeData` - 40 edges
3. `LemonadeCoordinator` - 38 edges
4. `LemonadeProfileSubentryFlow` - 34 edges
5. `LemonadeConfigFlow` - 30 edges
6. `LemonadeError` - 29 edges
7. `LemonadeOptionsFlow` - 29 edges
8. `RuntimeSetupTest` - 28 edges
9. `LemonadeAuthError` - 28 edges
10. `Any` - 27 edges

## Surprising Connections (you probably didn't know these)
- `_VolMarker` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `str` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `Any` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `int` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `_VolSchema` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py

## Communities (41 total, 10 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (40): _async_chat_completion(), _async_generate_image(), async_register_services(), _async_text_to_speech(), _async_transcribe_audio(), _default_model(), _extract_chat_content(), _get_entry_and_client() (+32 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (55): bool, bytes, ClientSession, ConfigSubentryFlow, ConfigType, Exception, int, LemonadeAuthError (+47 more)

### Community 2 - "Community 2"
Cohesion: 0.25
Nodes (7): config, error, step, cannot_connect, invalid_auth, invalid_url, unknown

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (39): FlowResult, async_get_options_flow(), async_get_supported_subentry_types(), _async_validate_connection(), _entry(), _entry_current_value(), _llm_api_options(), _model_select_selector() (+31 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (39): LemonadeConfigFlow, LemonadeOptionsFlow, LemonadeProfileSubentryFlow, Handle a config flow for Lemonade Server., Handle Lemonade Server options., Handle Lemonade profile subentries., Initialize the subentry flow., Handle a config flow for Lemonade Server. (+31 more)

### Community 5 - "Community 5"
Cohesion: 0.17
Nodes (11): after_dependencies, codeowners, config_flow, dependencies, documentation, domain, integration_type, iot_class (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.16
Nodes (16): all_model_ids(), _capabilities(), is_llm(), _labels(), LemonadeModel, Any, bool, str (+8 more)

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
Cohesion: 0.23
Nodes (11): _async_delete_missing_capability_issues(), _async_update_missing_capability_issues(), str, Create or delete repair issues for missing optional capabilities., Delete repair issues for optional capabilities tied to an entry., async_create_missing_capability_issue(), async_delete_missing_capability_issue(), HomeAssistant (+3 more)

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (12): step, title, ai_task_data, conversation, step, title, description, title (+4 more)

### Community 27 - "Community 27"
Cohesion: 0.25
Nodes (8): api_key, default_ai_task_model, default_conversation_model, default_image_model, default_stt_model, default_tts_model, timeout, data

### Community 28 - "Community 28"
Cohesion: 0.48
Nodes (7): already_configured, entry_not_loaded, no_models, unknown_profile_type, abort, abort, abort

### Community 29 - "Community 29"
Cohesion: 0.43
Nodes (7): llm_hass_api, model, name, prompt, url, data, data

### Community 30 - "Community 30"
Cohesion: 0.33
Nodes (5): config_subentries, issues, missing_capability, description, title

### Community 31 - "Community 31"
Cohesion: 0.40
Nodes (5): description, title, options, step, init

### Community 32 - "Community 32"
Cohesion: 0.21
Nodes (8): catalog(), parse_models_response(), Parse a Lemonade models response into a capability catalog., LemonadeModelCatalog, _install_homeassistant_stubs(), ParseModelsResponseTest, Tests for Lemonade model parsing., Install minimal Home Assistant dependency stubs for unit tests.

### Community 37 - "Community 37"
Cohesion: 0.19
Nodes (9): ConfigEntry, HomeAssistant, LemonadeClient, Initialize the coordinator., LemonadeModelCatalog, Parsed Lemonade models grouped by capability., Return models for a capability., Return model IDs for a capability. (+1 more)

### Community 38 - "Community 38"
Cohesion: 0.26
Nodes (6): headers(), Async client for Lemonade Server's OpenAI-compatible API., Constants for the Lemonade Server integration., Data coordinator for Lemonade Server., The Lemonade Server integration., Repairs helpers for Lemonade Server.

### Community 39 - "Community 39"
Cohesion: 0.47
Nodes (5): health(), Any, str, Fetch Lemonade Server health and models., server_status()

### Community 40 - "Community 40"
Cohesion: 0.50
Nodes (4): get_default_model(), Return the configured default model for an entry., Return the configured default model for an entry., Return the configured default model for an entry.

## Knowledge Gaps
- **108 isolated node(s):** `bool`, `ClientSession`, `int`, `domain`, `name` (+103 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LemonadeClient` connect `Community 1` to `Community 0`, `Community 32`, `Community 3`, `Community 4`, `Community 37`, `Community 38`, `Community 39`, `Community 25`?**
  _High betweenness centrality (0.192) - this node is a cross-community bridge._
- **Why does `LemonadeCoordinator` connect `Community 4` to `Community 1`, `Community 37`, `Community 38`, `Community 39`, `Community 25`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `parse_models_response()` connect `Community 32` to `Community 38`, `Community 37`, `Community 6`, `Community 39`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `LemonadeClient` (e.g. with `_VolMarker` and `str`) actually correct?**
  _`LemonadeClient` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `LemonadeRuntimeData` (e.g. with `_VolMarker` and `str`) actually correct?**
  _`LemonadeRuntimeData` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `LemonadeCoordinator` (e.g. with `_VolMarker` and `str`) actually correct?**
  _`LemonadeCoordinator` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `LemonadeProfileSubentryFlow` (e.g. with `_VolMarker` and `str`) actually correct?**
  _`LemonadeProfileSubentryFlow` has 23 INFERRED edges - model-reasoned connections that need verification._