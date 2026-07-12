# Task 2 Report — Collapse transcription outcome ladders

## Changed files

- `custom_components/lemonade/speech.py`
- `custom_components/lemonade/stt.py`
- `custom_components/lemonade/services.py`
- `tests/test_runtime.py`

## Design choices

- Replaced both transcription ladders with one frozen `SpeechTranscriptionSuccess | SpeechTranscriptionFailure` union.
- Success carries only validated text and the raw Lemonade response.
- Failure carries the exception and, when parsing reached a response, that raw response. STT client exceptions use the same failure case without inventing response data.
- Removed validity flags, nullable base text, abstract throwing accessors, the nested transcription result, and the adapter-specific result family.
- Made both Home Assistant adapters branch exhaustively over the closed outcome with `assert_never`.
- Preserved direct-service invalid-response output as `{"text": None, "response": response}` and preserved its existing client-error translation path.

## TDD and verification

- Red: focused outcome tests failed because parsing still returned `ValidSpeechTranscription` / `InvalidSpeechTranscription`.
- Green: `python3 -m unittest tests.test_runtime -q` — 140 tests ran, OK.
- `python3 -m compileall -q custom_components/lemonade` — exit 0, no output.
- `git diff --check` — exit 0, no output.

## Commit

- Implementation: `c4e6c7e` (`Collapse speech transcription outcomes`)

## Concerns

- None.
