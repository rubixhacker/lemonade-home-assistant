# Architecture Review Findings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Concentrate repeated Server Entry policy behind deep modules and remove compatibility-only seams that no production caller uses.

**Architecture:** `connection.py` owns Lemonade client construction, health probing, and low-level failure classification; config flow and entry setup retain their distinct Home Assistant translations. `server_capabilities.py` becomes the sole Server Entry capability interface, while speech and image-generation tests cross their production modules rather than legacy adapters.

**Tech Stack:** Python 3, Home Assistant custom integration, `unittest`, `aiohttp`.

## Global Constraints

- Preserve existing Home Assistant config-flow keys: `invalid_auth`, `cannot_connect`, and `unknown`.
- Preserve setup lifecycle translation: authentication failures are `ConfigEntryAuthFailed`; transport failures are `ConfigEntryNotReady`; other Lemonade failures are `ConfigEntryError`.
- Keep URL syntax validation in `config_flow.py`; it is not connection-probe policy.
- Do not remove the existing outer setup timeout without a regression test and an explicit behavior decision.
- Do not change the supported Home Assistant integration interface or add a public third-party Python import contract.
- Do not implement the speculative Direct Services or broad test-adapter candidates in this batch.

---

### Task 1: Deepen Server Entry connection policy

**Files:**
- Create: `custom_components/lemonade/connection.py`
- Modify: `custom_components/lemonade/__init__.py`
- Modify: `custom_components/lemonade/config_flow.py`
- Modify: `tests/test_runtime.py`

**Interfaces:**
- Produces `ConnectionSettings`, `ConnectionFailureKind`, `ConnectionProbeError`, and `async_create_verified_client(session, settings)` from `connection.py`.
- Config flow maps probe classifications to form keys; entry setup maps the same classifications to Home Assistant lifecycle exceptions.

- [ ] **Step 1: Write failing connection-policy tests**

Add focused tests proving a supplied fake client/session is built from normalized URL, API key, timeout, and SSL settings; `LemonadeAuthError` is classified before `LemonadeError`; `TimeoutError`, `aiohttp.ClientError`, and `ConnectionError` classify as transport; another `LemonadeError` classifies as server; an unexpected exception classifies as unknown. Add adapter-level tests for config-flow mappings and entry-setup mappings listed in Global Constraints.

- [ ] **Step 2: Run the focused tests and verify red**

Run: `python3 -m unittest tests.test_runtime.RuntimeSetupTest -v`

Expected: failures naming missing `lemonade.connection` exports or the old duplicated adapter behavior.

- [ ] **Step 3: Add the deep connection module and migrate adapters**

Implement immutable settings and classified probe errors in `connection.py`. `async_create_verified_client` must instantiate `LemonadeClient`, await `health()`, and return the ready client or raise a classified `ConnectionProbeError`. Keep low-level taxonomy in that module. In `__init__.py`, resolve options-over-data then translate only the classified result. In `config_flow.py`, retain local URL validation and translate only the classified result to existing form keys.

- [ ] **Step 4: Verify green and regression coverage**

Run: `python3 -m unittest tests.test_runtime -v`

Expected: all runtime tests pass, including setup option precedence and config-flow connection error mapping.

- [ ] **Step 5: Commit**

Run: `git add custom_components/lemonade/connection.py custom_components/lemonade/__init__.py custom_components/lemonade/config_flow.py tests/test_runtime.py && git commit -m "refactor: centralize server connection policy"`

### Task 2: Close the Server Entry capability seam

**Files:**
- Delete: `custom_components/lemonade/model_resolution.py`
- Modify: `custom_components/lemonade/const.py`
- Modify: `custom_components/lemonade/config_flow.py`
- Modify: `custom_components/lemonade/profile_chat.py`
- Modify: `custom_components/lemonade/services.py`
- Modify: `custom_components/lemonade/speech.py`
- Modify: `tests/test_models.py`
- Modify: `tests/test_runtime.py`

**Interfaces:**
- `server_capabilities.py` is the single capability interface for `RuntimeCapabilityView`, `runtime_model_view`, catalog inspection, and entry-model resolution.
- `const.py` retains raw Home Assistant/Lemonade literals only; it no longer re-exports Server Entry capability policy.

- [ ] **Step 1: Write failing migration tests**

Change capability tests to import and exercise `catalog_model_ids`, `RuntimeCapabilityView.resolve_model`, and `runtime_model_view` directly from `lemonade.server_capabilities`. Add an assertion that `lemonade.const` does not expose the capability-policy re-export surface. Retain all existing catalog ordering, Model Selector fallback, and repair-presentation behavior assertions.

- [ ] **Step 2: Run focused model and runtime tests and verify red**

Run: `python3 -m unittest tests.test_models tests.test_runtime -v`

Expected: failures while production callers and tests still import `model_resolution` or capability policy through `const`.

- [ ] **Step 3: Make `server_capabilities.py` the canonical interface**

Move all imports in production callers and tests from `model_resolution.py` to `server_capabilities.py`. Replace the wrapper-only `resolve_model` and `resolve_entry_model` calls with `RuntimeCapabilityView(...).resolve_model(...)` and `runtime_model_view(entry).resolve_entry_model(...)`. Import Model Selector policy directly from `server_capabilities.py`, remove the capability-policy re-export block from `const.py`, then delete `model_resolution.py`.

- [ ] **Step 4: Verify green and absence of retired seams**

Run: `python3 -m unittest tests.test_models tests.test_runtime -v && rg -n "model_resolution|default_model_capability_presentations" custom_components tests --glob '*.py'`

Expected: 137 tests pass; no `model_resolution` import remains; only direct `server_capabilities` capability-policy imports remain.

- [ ] **Step 5: Commit**

Run: `git add custom_components/lemonade tests/test_models.py tests/test_runtime.py && git commit -m "refactor: consolidate server capability interface"`

### Task 3: Retire verified test-only compatibility adapters

**Files:**
- Delete: `custom_components/lemonade/voice.py`
- Delete: `custom_components/lemonade/transcription.py`
- Modify: `custom_components/lemonade/image_result.py`
- Modify: `custom_components/lemonade/services.py`
- Modify: `tests/test_runtime.py`

**Interfaces:**
- Tests import canonical speech interfaces from `speech.py` and image artifacts from `ImageGenerationResult`.
- Production image generation stays in `image_result.py`; only its test-only convenience functions are retired.

- [ ] **Step 1: Write failing canonical-interface tests**

Rewrite adapter-specific tests to import `SpeechTranscriptionRequest`, `parse_speech_transcription_result`, `request_speech_transcription`, and `speech_transcription_outcome` from `lemonade.speech`. For image artifacts, assert through `ImageGenerationResult.artifact` or `require_artifact()` rather than `generated_image_artifact`. Preserve valid and invalid transcription outcome behavior and image save/no-save behavior.

- [ ] **Step 2: Run focused tests and verify red**

Run: `python3 -m unittest tests.test_runtime -v`

Expected: tests fail until they and production callers no longer rely on compatibility aliases.

- [ ] **Step 3: Delete only proven compatibility seams**

Delete `voice.py` and `transcription.py`. Remove `generated_image_artifact` and `image_bytes_and_extension` from `image_result.py`, and remove the sole `extract_image_bytes` wrapper from `services.py`. Keep `image_result.py`, `ImageGenerationRequest`, `ImageGenerationResult`, and `generate_image` unchanged as production interfaces.

- [ ] **Step 4: Verify green and no stale references**

Run: `python3 -m unittest tests.test_models tests.test_runtime -v && ! rg -n "lemonade\\.(voice|transcription)|generated_image_artifact|image_bytes_and_extension|extract_image_bytes" custom_components tests --glob '*.py'`

Expected: all 137 tests pass and the retired compatibility names have no repository references.

- [ ] **Step 5: Commit**

Run: `git add custom_components/lemonade tests/test_runtime.py && git commit -m "refactor: remove test-only compatibility adapters"`

## Verification

- Run `python3 -m unittest tests.test_models tests.test_runtime -v` from the isolated worktree.
- Run `python3 -m compileall -q custom_components/lemonade`.
- Review the complete branch diff against this plan before handoff.
