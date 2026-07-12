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
- Direct response content uses the LLM module's canonical `response_assistant_content` projection; it reads valid first-message text independently of optional tool-call parsing, preserving direct-service behavior when tool metadata is malformed or unsupported. The duplicate service parser was removed.
- Existing service schema, returned `{"content", "response"}` mapping, prompt-required error, and model/temperature/token behavior remain unchanged.

## Tests

- `python3 -m unittest tests.test_runtime -q` — PASS, 139 tests in 0.102s.
- `python3 -m compileall -q custom_components/lemonade` — PASS, no output.
- `git diff --check` — PASS, no output.
- Reviewer fix: `python3 -m unittest tests.test_runtime -q` — PASS, 140 tests in 0.107s, including malformed tool-call metadata regression coverage.
- Reviewer fix: `python3 -m compileall -q custom_components/lemonade` — PASS, no output.
- Reviewer fix: `git diff --check` — PASS, no output.

## Commit

- Initial task commit: `bbafe737cf11ae30b9db4897519eab668478699f`.
- Reviewer fix commit: `d6c547064bf2d21e8e6e7b14be73bb8718f1a856`.

## Concerns

- None.
