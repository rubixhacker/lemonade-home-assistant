# Pass 2 Task 1 Report — Canonical catalog seam

## Result

Completed against base `9248a5bf7dba2475af2cd1fd4b9789ccd9528468`.

Implementation commit: `533b42a`

- `RuntimeCapabilityView` now owns `LemonadeModelCatalog` and delegates directly to its canonical operations.
- Removed duck-typed `model_ids`, `models_for`, `models`, and `all_model_ids` compatibility adapters.
- Preserved production source adaptation through runtime views, config-entry runtime data/coordinators, runtime state, coordinators, and canonical catalogs.
- Preserved legitimate empty state only through a real coordinator owning an empty canonical catalog.
- Invalid source wiring now raises a deterministic `TypeError` rather than silently behaving as an empty catalog.
- Replaced catalog test doubles with immutable `LemonadeModelCatalog` fixtures.

## TDD evidence

The new empty-versus-malformed source test failed first because malformed wiring still silently returned an empty catalog. Reviewer follow-up added regression coverage proving that missing and `None` coordinators fail deterministically, while a real coordinator with an empty canonical catalog remains valid.

## Verification

- `python3 -m unittest tests.test_models tests.test_runtime -q` — 154 tests passed.
- `python3 -m compileall -q custom_components/lemonade` — passed.
- `git diff --check` — passed.

## Self-review

No production caller gained an adapter or compatibility branch. Ordering and capability behavior remain owned by `LemonadeModelCatalog`; selector, resolution, count, degraded-policy, repair, and unavailable-entry tests pass in the combined suite.
