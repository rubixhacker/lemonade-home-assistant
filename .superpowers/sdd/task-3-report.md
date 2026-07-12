# Task 3 Report — Canonical Server Entry runtime state

## Changed files

- `custom_components/lemonade/coordinator.py`
- `custom_components/lemonade/models.py`
- `tests/test_runtime.py`

## Representation decisions

- `LemonadeRuntimeState` now stores only canonical parsed values: semantic `server_status` and `LemonadeModelCatalog`.
- Raw health and model payloads are discarded after parsing because no production caller consumes them.
- `model_view` is a derived property over the canonical catalog, so callers cannot construct catalog/view disagreement.
- The model response is parsed exactly once at the refresh-state construction seam.

## Tests and exact results

- `python3 -m unittest tests.test_runtime -q`: 143 tests, OK.
- `python3 -m compileall -q custom_components/lemonade`: exit 0.
- `git diff --check`: exit 0.
- Required combined command `python3 -m unittest tests.test_models tests.test_runtime -q`: 144 tests run, FAILED with one import error while loading `tests.test_models` (`ModuleNotFoundError: No module named 'homeassistant.components'`). The same error reproduces on unmodified `tests.test_models` alone and is outside Task 3's focused runtime-test scope.

## Commits

- `40ecc06` — Canonicalize Server Entry runtime state

## Concerns

- None. The combined-suite import coupling was fixed by Task 1 and the controller subsequently ran the combined suite successfully.

## Reviewer fix

- Removed the unused `LemonadeModel.raw` reference to untrusted caller-owned mappings.
- Made `LemonadeModelCatalog.models` detach from caller containers and made `by_capability` an immutable projection derived from canonical model values.
- Added regression coverage proving mutations to the original model record, labels list, and response list cannot change runtime state; also verified the capability index rejects mutation.
- Extended deletion assertions for retired runtime `health`, `raw_models`, and stored `model_view` fields without rejecting the derived `model_view` property.
- Commit: `09bb038` — Freeze canonical runtime model catalog.
- Verification: `python3 -m unittest tests.test_runtime -q` ran 144 tests, OK; `python3 -m compileall -q custom_components/lemonade` and `git diff --check` exited 0.
- The required combined command ran 145 tests but retained the inherited `tests.test_models` import error (`homeassistant.components` missing); the same import error reproduces with `tests.test_models` alone.
- Final integrated evidence after Task 1's import-coupling fix: the controller ran the combined suite successfully with 153 tests.
