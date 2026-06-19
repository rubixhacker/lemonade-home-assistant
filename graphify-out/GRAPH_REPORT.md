# Graph Report - lemonade-core-quality  (2026-06-19)

## Corpus Check
- 24 files · ~17,987 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 862 nodes · 1728 edges · 77 communities (48 shown, 29 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 297 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9db5af9e`
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
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]

## God Nodes (most connected - your core abstractions)
1. `LemonadeError` - 83 edges
2. `LemonadeClient` - 76 edges
3. `RuntimeSetupTest` - 63 edges
4. `FakeCatalog` - 45 edges
5. `LemonadeCoordinator` - 43 edges
6. `LemonadeRuntimeData` - 41 edges
7. `_require_module()` - 35 edges
8. `LemonadeProfileSubentryFlow` - 35 edges
9. `LemonadeConfigFlow` - 31 edges
10. `Any` - 30 edges

## Surprising Connections (you probably didn't know these)
- `_VolMarker` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `_VolMarker` --uses--> `LemonadeError`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `str` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `str` --uses--> `LemonadeRuntimeData`  [INFERRED]
  tests/test_runtime.py → lemonade/data.py
- `str` --uses--> `LemonadeProfileSubentryFlow`  [INFERRED]
  tests/test_runtime.py → lemonade/config_flow.py

## Communities (77 total, 29 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (39): _async_chat_completion(), _async_generate_image(), async_register_services(), _async_text_to_speech(), _async_transcribe_audio(), _default_model(), _extract_chat_content(), _get_entry_and_client() (+31 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (27): bytes, ClientSession, int, headers(), Any, bytes, float, int (+19 more)

### Community 2 - "Community 2"
Cohesion: 0.17
Nodes (15): async_setup_entry(), LemonadeCapabilityCountSensor, LemonadeSensor, LemonadeServerStatusSensor, LemonadeTotalModelCountSensor, AddEntitiesCallback, HomeAssistant, Sensor entities for Lemonade Server. (+7 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (36): FlowResult, _async_validate_connection(), _entry_current_value(), _llm_api_options(), _model_select_selector(), _profile_type(), Any, str (+28 more)

### Community 4 - "Community 4"
Cohesion: 0.19
Nodes (23): LemonadeConfigFlow, LemonadeOptionsFlow, LemonadeProfileSubentryFlow, Handle a config flow for Lemonade Server., Handle Lemonade Server options., Handle Lemonade profile subentries., Initialize the subentry flow., Handle a config flow for Lemonade Server. (+15 more)

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
Cohesion: 0.16
Nodes (10): Async client for Lemonade Server's OpenAI-compatible API., Constants for the Lemonade Server integration., Data coordinator for Lemonade Server., Base entities for Lemonade Server., is_llm(), bool, Model catalog parsing for Lemonade Server., Repairs helpers for Lemonade Server. (+2 more)

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
Cohesion: 0.18
Nodes (12): _ai_task_subentries(), async_setup_entry(), _maybe_await(), AddEntitiesCallback, HomeAssistant, LemonadeConfigEntry, Return AI task profile subentries from a config entry., Return AI task profile subentries from a config entry. (+4 more)

### Community 30 - "Community 30"
Cohesion: 0.15
Nodes (13): name, sensor, name, name, conversation_model_count, image_model_count, model_count, server_status (+5 more)

### Community 38 - "Community 38"
Cohesion: 0.15
Nodes (13): async_setup_entry(), current_option(), LemonadeDefaultModelSelect, options(), AddEntitiesCallback, HomeAssistant, LemonadeConfigEntry, str (+5 more)

### Community 43 - "Community 43"
Cohesion: 0.21
Nodes (12): _decode_image_response(), _decode_image_value(), _image_response_values(), Any, bytes, Yield image payload candidates from an OpenAI/Lemonade response., Yield image payload candidates from an OpenAI/Lemonade response., Decode one image value into bytes when possible. (+4 more)

### Community 44 - "Community 44"
Cohesion: 0.18
Nodes (10): LemonadeAITaskEntity, AI task entity backed by a Lemonade AI task profile., AI task entity backed by a Lemonade AI task profile., AI task entity backed by a Lemonade AI task profile., Return the configured image generation model., Return the configured image generation model., Return the configured image generation model., Generate an image for an AI task using Lemonade. (+2 more)

### Community 46 - "Community 46"
Cohesion: 0.08
Nodes (7): FakeCatalog, FakeEntry, FakeHass, _profile_flow(), _require_module(), RuntimeSetupTest, _schema_fields()

### Community 47 - "Community 47"
Cohesion: 0.22
Nodes (10): _first_catalog_model_id(), str, Return the model configured for this AI task profile., Return the model configured for this AI task profile., Return the model configured for this AI task profile., Return subentry data as a plain dict., Return subentry data as a plain dict., Return the first catalog model ID for a capability. (+2 more)

### Community 48 - "Community 48"
Cohesion: 0.29
Nodes (7): _final_assistant_content(), AI task platform for Lemonade Server profiles., Return a mapping key or attribute value from an object., Return a mapping key or attribute value from an object., Return the latest assistant text from a chat log., Return the latest assistant text from a chat log., _value()

### Community 49 - "Community 49"
Cohesion: 0.28
Nodes (6): LemonadeConfigEntry, Initialize the server status sensor., Initialize the model count sensor., Initialize the model count sensor., Initialize the capability count sensor., Initialize the capability count sensor.

### Community 50 - "Community 50"
Cohesion: 0.25
Nodes (7): config, error, step, cannot_connect, invalid_auth, invalid_url, unknown

### Community 51 - "Community 51"
Cohesion: 0.18
Nodes (11): api_key, default_ai_task_model, default_conversation_model, default_image_model, default_stt_model, default_tts_model, timeout, data (+3 more)

### Community 52 - "Community 52"
Cohesion: 0.48
Nodes (7): already_configured, entry_not_loaded, no_models, unknown_profile_type, abort, abort, abort

### Community 55 - "Community 55"
Cohesion: 0.43
Nodes (7): llm_hass_api, model, name, prompt, url, data, data

### Community 56 - "Community 56"
Cohesion: 0.25
Nodes (7): config_subentries, issues, missing_capability, description, title, options, step

### Community 57 - "Community 57"
Cohesion: 0.29
Nodes (6): _catalog_model_ids(), Decode the first image bytes from an image generation response., Initialize the AI task entity., Initialize the AI task entity., Return catalog model IDs for a capability., Return catalog model IDs for a capability.

### Community 58 - "Community 58"
Cohesion: 0.12
Nodes (6): _ConfigFlowBase, _ConfigSubentryFlowBase, FakeResponse, _FlowBase, Any, str

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (12): LemonadeEntity, LemonadeConfigEntry, str, Base entity for Lemonade Server platforms., Initialize the Lemonade entity., available(), bool, available() (+4 more)

### Community 60 - "Community 60"
Cohesion: 0.09
Nodes (32): _async_delete_missing_capability_issues(), async_setup(), async_setup_entry(), async_unload_entry(), _async_update_missing_capability_issues(), async_update_options(), get_default_model(), bool (+24 more)

### Community 61 - "Community 61"
Cohesion: 0.10
Nodes (21): async_setup_entry(), available(), _error_result(), _first_catalog_model_id(), LemonadeSTTEntity, AddEntitiesCallback, Any, bool (+13 more)

### Community 62 - "Community 62"
Cohesion: 0.19
Nodes (21): bool, ConfigSubentryFlow, ConfigType, Exception, LemonadeAuthError, LemonadeClient, LemonadeError, Base Lemonade API error. (+13 more)

### Community 63 - "Community 63"
Cohesion: 0.12
Nodes (20): async_setup_entry(), _audio_extension(), available(), _first_catalog_model_id(), LemonadeTTSEntity, AddEntitiesCallback, Any, bool (+12 more)

### Community 64 - "Community 64"
Cohesion: 0.17
Nodes (11): AudioBitRates, AudioChannels, AudioCodecs, AudioFormats, AudioSampleRates, Speech-to-text platform for Lemonade Server., supported_bit_rates(), supported_channels() (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.17
Nodes (12): name, name, name, name, name, entity, select, default_ai_task_model (+4 more)

### Community 67 - "Community 67"
Cohesion: 0.40
Nodes (5): _install_homeassistant_stubs(), Install minimal Home Assistant dependency stubs for unit tests., Install minimal Home Assistant dependency stubs for unit tests., Install minimal Home Assistant dependency stubs for unit tests., Install minimal Home Assistant dependency stubs for unit tests.

### Community 68 - "Community 68"
Cohesion: 0.50
Nodes (3): Generate data for an AI task using Lemonade., Generate data for an AI task using Lemonade., Generate data for an AI task using Lemonade.

## Knowledge Gaps
- **122 isolated node(s):** `bool`, `HomeAssistant`, `AddEntitiesCallback`, `bool`, `ClientSession` (+117 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LemonadeError` connect `Community 62` to `Community 64`, `Community 1`, `Community 66`, `Community 3`, `Community 4`, `Community 43`, `Community 44`, `Community 46`, `Community 47`, `Community 48`, `Community 61`, `Community 25`, `Community 58`, `Community 60`, `Community 29`, `Community 63`?**
  _High betweenness centrality (0.187) - this node is a cross-community bridge._
- **Why does `LemonadeClient` connect `Community 62` to `Community 0`, `Community 1`, `Community 66`, `Community 3`, `Community 4`, `Community 6`, `Community 46`, `Community 25`, `Community 58`, `Community 60`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `LemonadeCoordinator` connect `Community 4` to `Community 66`, `Community 6`, `Community 46`, `Community 25`, `Community 58`, `Community 59`, `Community 60`, `Community 62`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 70 inferred relationships involving `LemonadeError` (e.g. with `_VolMarker` and `str`) actually correct?**
  _`LemonadeError` has 70 INFERRED edges - model-reasoned connections that need verification._
- **Are the 56 inferred relationships involving `LemonadeClient` (e.g. with `_VolMarker` and `str`) actually correct?**
  _`LemonadeClient` has 56 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `RuntimeSetupTest` (e.g. with `LemonadeClient` and `LemonadeRuntimeData`) actually correct?**
  _`RuntimeSetupTest` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `FakeCatalog` (e.g. with `LemonadeClient` and `LemonadeRuntimeData`) actually correct?**
  _`FakeCatalog` has 7 INFERRED edges - model-reasoned connections that need verification._