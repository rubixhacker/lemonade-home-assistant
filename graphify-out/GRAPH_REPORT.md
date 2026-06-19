# Graph Report - lemonade-home-assistant  (2026-06-18)

## Corpus Check
- 8 files · ~2,187 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 133 nodes · 258 edges · 8 communities (7 shown, 1 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 10|Community 10]]

## God Nodes (most connected - your core abstractions)
1. `LemonadeClient` - 33 edges
2. `LemonadeError` - 19 edges
3. `LemonadeAuthError` - 18 edges
4. `_async_chat_completion()` - 11 edges
5. `_get_entry_and_client()` - 10 edges
6. `str` - 10 edges
7. `_async_generate_image()` - 9 edges
8. `_async_transcribe_audio()` - 9 edges
9. `_async_text_to_speech()` - 9 edges
10. `async_register_services()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `LemonadeClient` --uses--> `LemonadeClient`  [INFERRED]
  lemonade/services.py → lemonade/api.py
- `HomeAssistant` --uses--> `LemonadeClient`  [INFERRED]
  lemonade/services.py → lemonade/api.py
- `ServiceCall` --uses--> `LemonadeClient`  [INFERRED]
  lemonade/services.py → lemonade/api.py
- `ConfigEntry` --uses--> `LemonadeClient`  [INFERRED]
  lemonade/services.py → lemonade/api.py
- `str` --uses--> `LemonadeClient`  [INFERRED]
  lemonade/services.py → lemonade/api.py

## Communities (8 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.19
Nodes (25): _async_chat_completion(), _async_generate_image(), async_register_services(), _async_text_to_speech(), _async_transcribe_audio(), _default_model(), _extract_chat_content(), _get_entry_and_client() (+17 more)

### Community 1 - "Community 1"
Cohesion: 0.16
Nodes (16): bytes, ClientSession, int, LemonadeClient, Any, float, str, Return Lemonade Server health. (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (18): already_configured, config, abort, error, step, api_key, model, name (+10 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (23): Exception, FlowResult, headers(), LemonadeAuthError, LemonadeError, Async client for Lemonade Server's OpenAI-compatible API., Base Lemonade API error., Lemonade API authentication error. (+15 more)

### Community 4 - "Community 4"
Cohesion: 0.19
Nodes (15): bool, ConfigType, async_setup(), async_setup_entry(), async_unload_entry(), async_update_options(), get_default_model(), ConfigEntry (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.20
Nodes (9): codeowners, config_flow, documentation, domain, integration_type, iot_class, name, requirements (+1 more)

### Community 7 - "Community 7"
Cohesion: 0.22
Nodes (8): Add from UI, code:text (/config/custom_components/lemonade/), code:text (http://192.168.1.10:13305), code:text (http://localhost:13305), Install, Lemonade Server Home Assistant custom integration, Next planned native Home Assistant platforms, Services

## Knowledge Gaps
- **28 isolated node(s):** `ClientSession`, `int`, `domain`, `name`, `version` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LemonadeClient` connect `Community 1` to `Community 0`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.273) - this node is a cross-community bridge._
- **Why does `LemonadeError` connect `Community 3` to `Community 1`, `Community 4`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `LemonadeAuthError` connect `Community 3` to `Community 1`, `Community 4`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `LemonadeClient` (e.g. with `HomeAssistant` and `ServiceCall`) actually correct?**
  _`LemonadeClient` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `LemonadeError` (e.g. with `HomeAssistant` and `ConfigType`) actually correct?**
  _`LemonadeError` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `LemonadeAuthError` (e.g. with `HomeAssistant` and `ConfigType`) actually correct?**
  _`LemonadeAuthError` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Custom services for Lemonade Server.`, `Return the selected config entry and client for a service call.`, `Return an entry's configured default model.` to the rest of the system?**
  _65 weakly-connected nodes found - possible documentation gaps or missing edges._