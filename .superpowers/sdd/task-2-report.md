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
- Initial report: `25bc2cd` (`Document speech outcome implementation`). The report
  was committed separately so it could record the exact implementation SHA.
- Reviewer test fix: `c0c7f8e` (`Test direct transcription outcome matrix`).
- This follow-up report update is committed separately after the reviewer test fix;
  its exact SHA is reported to the controller on completion.

## Reviewer follow-up evidence

- Replaced the patched invalid-response service test with a data-driven matrix
  that exercises the real fake client, file buffering, transcription request,
  response parser, and direct-service adapter.
- Covered valid text, `text: None`, missing text, and a non-mapping response.
- Asserted the complete `{"text": ..., "response": ...}` result and the complete
  client request for every case. The existing direct client-error matrix remains.
- Focused test: `python3 -m unittest tests.test_runtime.RuntimeSetupTest.test_transcribe_audio_service_preserves_parsed_response_outcomes -q`
  — 1 test ran, OK.
- Full test: `python3 -m unittest tests.test_runtime -q` — 140 tests ran, OK.
- `python3 -m compileall -q custom_components/lemonade` — exit 0, no output.
- `git diff --check` — exit 0, no output.

## Concerns

- None.
