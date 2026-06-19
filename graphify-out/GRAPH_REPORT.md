# Graph Report - lemonade-core-quality  (2026-06-19)

## Corpus Check
- 24 files · ~20,963 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 971 nodes · 2010 edges · 94 communities (57 shown, 37 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 347 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `86aae81d`
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
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]

## God Nodes (most connected - your core abstractions)
1. `LemonadeError` - 107 edges
2. `RuntimeSetupTest` - 82 edges
3. `LemonadeClient` - 82 edges
4. `FakeCatalog` - 55 edges
5. `LemonadeRuntimeData` - 48 edges
6. `_require_module()` - 45 edges
7. `LemonadeCoordinator` - 45 edges
8. `LemonadeProfileSubentryFlow` - 37 edges
9. `Any` - 33 edges
10. `LemonadeConfigFlow` - 33 edges

## Surprising Connections (you probably didn't know these)
- `_VolMarker` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `_VolMarker` --uses--> `LemonadeRuntimeData`  [INFERRED]
  tests/test_runtime.py → lemonade/data.py
- `_VolMarker` --uses--> `LemonadeError`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py
- `_VolMarker` --uses--> `LemonadeCoordinator`  [INFERRED]
  tests/test_runtime.py → lemonade/coordinator.py
- `str` --uses--> `LemonadeClient`  [INFERRED]
  tests/test_runtime.py → lemonade/api.py

## Communities (94 total, 37 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (18): _async_chat_completion(), _extract_chat_content(), _messages_from_call(), Custom services for Lemonade Server., Extract assistant content from an OpenAI-style chat response., Extract assistant content from an OpenAI-style chat response., Build OpenAI-compatible chat messages from service data., Build OpenAI-compatible chat messages from service data. (+10 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (27): bytes, ClientSession, int, headers(), Any, bytes, float, int (+19 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (47): LemonadeEntity, LemonadeConfigEntry, str, Base entity for Lemonade Server platforms., Initialize the Lemonade entity., async_setup_entry(), available(), current_option() (+39 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (31): FlowResult, _async_validate_connection(), _entry_current_value(), _profile_type(), Any, str, Config flow for Lemonade Server., Validate that Lemonade Server is reachable. (+23 more)

### Community 4 - "Community 4"
Cohesion: 0.18
Nodes (18): all_model_ids(), _capabilities(), is_llm(), _labels(), LemonadeModel, parse_models_response(), Any, bool (+10 more)

### Community 5 - "Community 5"
Cohesion: 0.17
Nodes (11): after_dependencies, codeowners, config_flow, dependencies, documentation, domain, integration_type, iot_class (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.40
Nodes (5): description, title, options, step, init

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (11): Add from UI, code:text (/config/custom_components/lemonade/), code:text (http://192.168.1.10:13305), code:text (http://localhost:13305), code:json ({), Generated image media, Install, Lemonade Server Home Assistant custom integration (+3 more)

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
Cohesion: 0.24
Nodes (7): Async client for Lemonade Server's OpenAI-compatible API., Constants for the Lemonade Server integration., Conversation platform for Lemonade Server profiles., Data coordinator for Lemonade Server., Base entities for Lemonade Server., The Lemonade Server integration., Text-to-speech platform for Lemonade Server.

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (12): step, title, ai_task_data, conversation, step, title, description, title (+4 more)

### Community 27 - "Community 27"
Cohesion: 0.06
Nodes (71): AssistantContentDeltaDict, HomeAssistantError, _arguments_to_dict(), _arguments_to_json(), _async_add_delta_content_stream(), _async_delta_stream(), async_handle_chat_log(), _attachment_mime_type() (+63 more)

### Community 28 - "Community 28"
Cohesion: 0.07
Nodes (31): async_setup_entry(), _conversation_subentries(), LemonadeConversationEntity, _maybe_await(), AddEntitiesCallback, Any, HomeAssistant, LemonadeConfigEntry (+23 more)

### Community 29 - "Community 29"
Cohesion: 0.25
Nodes (9): _ai_task_subentries(), async_setup_entry(), AddEntitiesCallback, HomeAssistant, LemonadeConfigEntry, Return AI task profile subentries from a config entry., Return AI task profile subentries from a config entry., Set up Lemonade AI task profile entities. (+1 more)

### Community 30 - "Community 30"
Cohesion: 0.08
Nodes (25): name, name, name, name, name, name, entity, select (+17 more)

### Community 38 - "Community 38"
Cohesion: 0.15
Nodes (23): LemonadeConfigFlow, LemonadeOptionsFlow, LemonadeProfileSubentryFlow, Handle a config flow for Lemonade Server., Handle Lemonade Server options., Handle Lemonade profile subentries., Initialize the subentry flow., Handle a config flow for Lemonade Server. (+15 more)

### Community 43 - "Community 43"
Cohesion: 0.21
Nodes (12): _decode_image_response(), _decode_image_value(), _image_response_values(), Any, bytes, Yield image payload candidates from an OpenAI/Lemonade response., Yield image payload candidates from an OpenAI/Lemonade response., Decode one image value into bytes when possible. (+4 more)

### Community 44 - "Community 44"
Cohesion: 0.40
Nodes (4): Generate an image for an AI task using Lemonade., Generate an image for an AI task using Lemonade., Generate an image for an AI task using Lemonade., Generate an image for an AI task using Lemonade.

### Community 46 - "Community 46"
Cohesion: 0.07
Nodes (7): FakeCatalog, FakeEntry, FakeHass, _profile_flow(), _require_module(), RuntimeSetupTest, _schema_fields()

### Community 47 - "Community 47"
Cohesion: 0.18
Nodes (10): LemonadeAITaskEntity, AI task entity backed by a Lemonade AI task profile., AI task entity backed by a Lemonade AI task profile., AI task entity backed by a Lemonade AI task profile., Return the model configured for this AI task profile., Return the model configured for this AI task profile., Return the model configured for this AI task profile., Generate data for an AI task using Lemonade. (+2 more)

### Community 48 - "Community 48"
Cohesion: 0.33
Nodes (7): _final_assistant_content(), str, Return a mapping key or attribute value from an object., Return a mapping key or attribute value from an object., Return the latest assistant text from a chat log., Return the latest assistant text from a chat log., _value()

### Community 49 - "Community 49"
Cohesion: 0.18
Nodes (27): bool, ConfigType, LemonadeAuthError, LemonadeClient, Lemonade API authentication error., Small async Lemonade Server API client., LemonadeCoordinator, Coordinate Lemonade Server health and model catalog updates. (+19 more)

### Community 50 - "Community 50"
Cohesion: 0.25
Nodes (7): config, error, step, cannot_connect, invalid_auth, invalid_url, unknown

### Community 51 - "Community 51"
Cohesion: 0.25
Nodes (8): api_key, default_ai_task_model, default_conversation_model, default_image_model, default_stt_model, default_tts_model, timeout, data

### Community 52 - "Community 52"
Cohesion: 0.48
Nodes (7): already_configured, entry_not_loaded, no_models, unknown_profile_type, abort, abort, abort

### Community 55 - "Community 55"
Cohesion: 0.43
Nodes (7): llm_hass_api, model, name, prompt, url, data, data

### Community 56 - "Community 56"
Cohesion: 0.33
Nodes (5): config_subentries, issues, missing_capability, description, title

### Community 57 - "Community 57"
Cohesion: 0.13
Nodes (20): ConfigSubentryFlow, Exception, LemonadeError, Base Lemonade API error., async_get_options_flow(), async_get_supported_subentry_types(), _entry(), _llm_api_options() (+12 more)

### Community 58 - "Community 58"
Cohesion: 0.16
Nodes (11): catalog(), ConfigEntry, HomeAssistant, LemonadeClient, Initialize the coordinator., LemonadeModelCatalog, Parsed Lemonade models grouped by capability., Return models for a capability. (+3 more)

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (19): _decode_base64_image(), _decode_data_image_url(), _decode_image_value(), _extension_from_media_type(), extract_image_bytes(), Any, str, Return a safe file extension for an image media type. (+11 more)

### Community 60 - "Community 60"
Cohesion: 0.11
Nodes (7): _ConfigFlowBase, _ConfigSubentryFlowBase, FakeResponse, FakeSession, _FlowBase, Any, str

### Community 61 - "Community 61"
Cohesion: 0.06
Nodes (36): AudioBitRates, AudioChannels, AudioCodecs, AudioFormats, AudioSampleRates, async_setup_entry(), available(), _error_result() (+28 more)

### Community 63 - "Community 63"
Cohesion: 0.09
Nodes (25): async_setup_entry(), _audio_extension(), available(), _first_catalog_model_id(), LemonadeTTSEntity, AddEntitiesCallback, Any, bool (+17 more)

### Community 64 - "Community 64"
Cohesion: 0.32
Nodes (7): async_create_missing_capability_issue(), async_delete_missing_capability_issue(), HomeAssistant, str, Repairs helpers for Lemonade Server., Create a repair issue for a missing model capability., Delete a repair issue for a restored model capability.

### Community 80 - "Community 80"
Cohesion: 0.29
Nodes (6): _catalog_model_ids(), Decode the first image bytes from an image generation response., Initialize the AI task entity., Initialize the AI task entity., Return catalog model IDs for a capability., Return catalog model IDs for a capability.

### Community 81 - "Community 81"
Cohesion: 0.47
Nodes (5): health(), Any, str, Fetch Lemonade Server health and models., server_status()

### Community 82 - "Community 82"
Cohesion: 0.14
Nodes (18): async_register_services(), _async_text_to_speech(), _get_entry_and_client(), HomeAssistant, Return the selected config entry and client for a service call., Handle lemonade.text_to_speech., Handle lemonade.text_to_speech., Register Lemonade custom services. (+10 more)

### Community 83 - "Community 83"
Cohesion: 0.25
Nodes (7): _maybe_await(), AI task platform for Lemonade Server profiles., Return subentry data as a plain dict., Return subentry data as a plain dict., Await a value only when it is awaitable., Await a value only when it is awaitable., _subentry_data()

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (6): _first_catalog_model_id(), Return the configured image generation model., Return the configured image generation model., Return the configured image generation model., Return the first catalog model ID for a capability., Return the first catalog model ID for a capability.

### Community 85 - "Community 85"
Cohesion: 0.23
Nodes (3): FakeServiceHass, Path, _service_entry()

### Community 86 - "Community 86"
Cohesion: 0.20
Nodes (10): _async_delete_missing_capability_issues(), async_unload_entry(), get_default_model(), Unload a Lemonade Server config entry., Unload a Lemonade Server config entry., Unload a Lemonade Server config entry., Return the configured default model for an entry., Set up Lemonade Server from a config entry. (+2 more)

### Community 87 - "Community 87"
Cohesion: 0.22
Nodes (10): _async_transcribe_audio(), _default_model(), Return an entry's configured default model., Return the selected config entry and client for a service call., Handle lemonade.transcribe_audio., Return a safe file extension for an image media type., Handle lemonade.transcribe_audio., Handle lemonade.transcribe_audio. (+2 more)

### Community 88 - "Community 88"
Cohesion: 0.22
Nodes (9): _async_generate_image(), _client_error(), Handle lemonade.generate_image., Return a UTC timestamp slug for generated media filenames., Return a UTC timestamp slug for generated media filenames., Return a Home Assistant service error for a Lemonade client failure., Handle lemonade.generate_image., Handle lemonade.generate_image. (+1 more)

### Community 89 - "Community 89"
Cohesion: 0.22
Nodes (4): _install_homeassistant_stubs(), ParseModelsResponseTest, Tests for Lemonade model parsing., Install minimal Home Assistant dependency stubs for unit tests.

### Community 90 - "Community 90"
Cohesion: 0.33
Nodes (6): _first_catalog_model_id(), Return the first model ID in the runtime catalog for a capability., Return the first model ID in the runtime catalog for a capability., Resolve a direct service model from request, defaults, or catalog., Resolve a direct service model from request, defaults, or catalog., _resolve_service_model()

### Community 91 - "Community 91"
Cohesion: 0.40
Nodes (5): async_update_options(), Reload Lemonade Server when options are updated., Reload Lemonade Server when options are updated., Reload Lemonade Server when options are updated., Reload Lemonade Server when options are updated.

### Community 92 - "Community 92"
Cohesion: 0.67
Nodes (3): Create parent directories and write image bytes., Create parent directories and write image bytes., _write_image_file()

## Knowledge Gaps
- **122 isolated node(s):** `bool`, `bool`, `ClientSession`, `int`, `domain` (+117 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LemonadeError` connect `Community 57` to `Community 0`, `Community 1`, `Community 3`, `Community 25`, `Community 27`, `Community 28`, `Community 29`, `Community 38`, `Community 43`, `Community 46`, `Community 47`, `Community 48`, `Community 49`, `Community 59`, `Community 60`, `Community 61`, `Community 63`, `Community 65`, `Community 82`, `Community 83`, `Community 85`?**
  _High betweenness centrality (0.218) - this node is a cross-community bridge._
- **Why does `LemonadeClient` connect `Community 49` to `Community 0`, `Community 1`, `Community 65`, `Community 3`, `Community 38`, `Community 27`, `Community 46`, `Community 81`, `Community 82`, `Community 85`, `Community 25`, `Community 58`, `Community 59`, `Community 60`, `Community 57`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `HomeAssistantError` connect `Community 27` to `Community 0`, `Community 44`, `Community 47`, `Community 49`, `Community 82`, `Community 84`, `Community 87`, `Community 88`, `Community 57`, `Community 90`, `Community 28`, `Community 63`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `LemonadeError` (e.g. with `Exception` and `_VolMarker`) actually correct?**
  _`LemonadeError` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `RuntimeSetupTest` (e.g. with `LemonadeClient` and `LemonadeRuntimeData`) actually correct?**
  _`RuntimeSetupTest` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 62 inferred relationships involving `LemonadeClient` (e.g. with `_VolMarker` and `str`) actually correct?**
  _`LemonadeClient` has 62 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `FakeCatalog` (e.g. with `LemonadeClient` and `LemonadeRuntimeData`) actually correct?**
  _`FakeCatalog` has 7 INFERRED edges - model-reasoned connections that need verification._