# Task 1 Report — Normalize direct chat at the intake seam

## Changed files

- `custom_components/lemonade/service_requests.py`
- `custom_components/lemonade/services.py`
- `custom_components/lemonade/llm.py`
- `custom_components/lemonade/chat_messages.py`
- `tests/test_runtime.py`

## Design choices

- `ChatCompletionRequest` now owns an immutable tuple of the closed normalized `Message` variants and parses raw service messages immediately with `parse_openai_message`.
- Prompt and system-prompt fallback constructs `UserMessage` and `SystemMessage` directly.
- The direct client adapter serializes each normalized message once with `serialize_message`; the request-specific deep freeze/thaw implementation was removed.
- Direct response content uses the LLM module's canonical `response_assistant_content` projection; it reads valid first-message text independently of optional tool-call parsing, preserving direct-service behavior when tool metadata is malformed or unsupported. The duplicate service parser was removed.
- Existing service schema, returned `{"content", "response"}` mapping, prompt-required error, and model/temperature/token behavior remain unchanged.
- The closed message algebra and OpenAI adapters live in HA-independent `chat_messages.py`; `llm.py` re-exports the public symbols and adds only HA conversation adaptation, preventing package/model imports from requiring `homeassistant.components`.
- Tool-call parsing preserves the pre-extraction first-present aliases: nested `arguments`, `args`, and `tool_args`, plus top-level `arguments`, `args`, `tool_args`, and `input`. Serialization projects every form to canonical OpenAI `function.arguments`.
- `response_message` in `chat_messages.py` is the single response-envelope selector reused by both assistant-content projection and HA delta conversion.

## Tests

- `python3 -m unittest tests.test_runtime -q` — PASS, 139 tests in 0.102s.
- `python3 -m compileall -q custom_components/lemonade` — PASS, no output.
- `git diff --check` — PASS, no output.
- Reviewer fix: `python3 -m unittest tests.test_runtime -q` — PASS, 140 tests in 0.107s, including malformed tool-call metadata regression coverage.
- Reviewer fix: `python3 -m compileall -q custom_components/lemonade` — PASS, no output.
- Reviewer fix: `git diff --check` — PASS, no output.
- Import-coupling fix: `python3 -m unittest tests.test_models tests.test_runtime -q` — PASS, 152 tests in 0.139s.
- Import-coupling fix: `python3 -m compileall -q custom_components/lemonade` — PASS, no output.
- Import-coupling fix: `git diff --check` — PASS, no output.
- Alias-parity fix: `python3 -m unittest tests.test_models tests.test_runtime -q` — PASS, 153 tests in 0.102s.
- Alias-parity fix: `python3 -m compileall -q custom_components/lemonade` — PASS, no output.
- Alias-parity fix: `git diff --check` — PASS, no output.

## Commit

- Initial task commit: `bbafe737cf11ae30b9db4897519eab668478699f`.
- Reviewer fix commit: `d6c547064bf2d21e8e6e7b14be73bb8718f1a856`.
- Import-coupling fix commit: `e125daa086ff34f6b87f71e6b016a976ae3db131`.
- Alias-parity fix commit: `2a43aa09f0052fe588bf2ba4b3d1406552ef4ecf`.

## Concerns

- None.
