# Task 4 Report — Finish the profile-field interpreter

## Changed files

- `custom_components/lemonade/profiles.py`
- `custom_components/lemonade/config_flow.py`
- `tests/test_runtime.py`

## Interpreter design

- `interpret_profile_field` is the one exhaustive match over the closed
  `ProfileFieldDefinition` cases. It projects each immutable field definition
  into adapter-neutral parsing and presentation instructions.
- `normalize_profile_field` executes those parsing instructions generically;
  `normalize_profile_data` applies them to a profile definition before typed
  profile construction. This removes persisted-key-specific parsing helpers.
- `config_flow.py` adapts the neutral presentation enum to Home Assistant
  selectors and markers, keeping Home Assistant types out of domain data.
- The table-driven matrix covers every field occurrence across Conversation
  Profile and AI Task Profile, including required/default/minimum/suggestion
  metadata, normalized persisted values, and presentation projections.

## TDD and deletion test

- Red: the new interpreter matrix failed to import
  `ProfileFieldPresentation` before implementation.
- Green: focused interpreter, parsing, schema, and reconfigure tests passed.
- Deletion test: weakening the below-minimum number rule made the matrix fail
  because Conversation Profile `max_history=-3` normalized to `20` instead of
  `0`. Restoring the interpreted minimum rule returned the focused slice to
  green.
- Standards review: PASS, no actionable documented-standard or smell findings.
- Spec review: PASS, no missing, incorrect, or out-of-scope behavior found.

## Exact verification

- `python3 -m unittest tests.test_models tests.test_runtime -q` — PASS, 153 tests
  in 0.106s.
- `python3 -m compileall -q custom_components/lemonade` — PASS, no output.
- `git diff --check` — PASS, no output.

## Commit

- Implementation: `9fb3a693176e3722e2b5774545400617108c9c55`
- Report: `f82d590735bb6adfd38bb848a77156d509fe56dd`

## Concerns

- The configured 1Password signing agent failed while writing the commit, so
  the implementation commit was created unsigned after verification.
