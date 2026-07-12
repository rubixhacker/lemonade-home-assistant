# Task 1 Report — Normalize direct chat at the intake seam

## Changed files

- `custom_components/lemonade/service_requests.py`
- `custom_components/lemonade/services.py`
- `custom_components/lemonade/llm.py`
- `tests/test_runtime.py`

## Design choices

- `ChatCompletionRequest` now owns an immutable tuple of the closed normalized `Message` variants and parses raw service messages immediately with `parse_message`.
- Prompt and system-prompt fallback constructs `UserMessage` and `SystemMessage` directly.
- The direct client adapter serializes each normalized message once with `serialize_message`; the request-specific deep freeze/thaw implementation was removed.
- Direct response content uses the LLM module's canonical response-to-delta projection through `response_assistant_content`; the duplicate service parser was removed.
- Existing service schema, returned `{"content", "response"}` mapping, prompt-required error, and model/temperature/token behavior remain unchanged.

## Tests

- `python3 -m unittest tests.test_runtime -q` — PASS, 139 tests in 0.102s.
- `python3 -m compileall -q custom_components/lemonade` — PASS, no output.
- `git diff --check` — PASS, no output.

## Commit

- This task's focused commit (SHA recorded in the controller handoff).

## Concerns

- None.
