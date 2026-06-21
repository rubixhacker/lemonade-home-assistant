# Release smoke checklist

Use this checklist before publishing a Lemonade Server Home Assistant beta or stable release.

## Current target

- Tag: `v0.2.14-beta.1`
- Manifest version: `0.2.14-beta.1`
- Install source: built HACS release artifact, not a direct working-tree copy
- Lemonade source: real Lemonade Server, not a fake endpoint

## Local package checks

Run from the repository root:

```bash
python3 -m unittest tests.test_models tests.test_runtime -v
python3 -m py_compile custom_components/lemonade/*.py
python3 -m json.tool custom_components/lemonade/manifest.json >/tmp/lemonade-manifest.json
python3 -m json.tool custom_components/lemonade/strings.json >/tmp/lemonade-strings.json
python3 -m json.tool custom_components/lemonade/translations/en.json >/tmp/lemonade-en.json
scripts/build-hacs-release.sh
unzip -t dist/lemonade.zip
unzip -l dist/lemonade.zip | grep "custom_components/lemonade/manifest.json"
unzip -l dist/lemonade.zip | grep "custom_components/lemonade/brand/icon.png"
```

Expected result:

- Unit tests pass.
- Python files compile.
- JSON files validate.
- `dist/lemonade.zip` contains `custom_components/lemonade/`.
- The artifact contains `manifest.json`, `strings.json`, `translations/en.json`, and `brand/icon.png`.

## Home Assistant smoke

Install `dist/lemonade.zip` into a Home Assistant instance as the release artifact under test, then restart Home Assistant.

Use a real Lemonade Server URL reachable from Home Assistant. The server must have at least one downloaded chat-capable model. Image, TTS, and STT checks are conditional on the models Lemonade advertises through `/v1/models`.

### Required checks

- Add a Lemonade Server Entry from the UI.
- Confirm the integration loads without startup errors.
- Confirm the integration page shows status and model-count entities.
- Create one Conversation Profile.
- Select the Conversation Profile in Assist or a voice pipeline.
- Send one Assist prompt and confirm a response is returned.
- Create one AI Task Profile.
- Run one AI task data-generation path and confirm a response is returned.
- Confirm direct service schemas are visible for:
  - `lemonade.chat_completion`
  - `lemonade.generate_image`
  - `lemonade.transcribe_audio`
  - `lemonade.text_to_speech`

### Conditional checks

If Lemonade advertises an image-generation model:

- Run `lemonade.generate_image` with `save: true`.
- Confirm the service response includes a `media_path`.
- Confirm the file is written under Home Assistant media storage.

If Lemonade advertises a TTS model:

- Confirm the Lemonade Server TTS entity is available.
- Generate speech through the native TTS path or `lemonade.text_to_speech`.
- Confirm audio data is returned.

If Lemonade advertises an STT model with `stt`, `transcription`, or `speech-to-text` metadata:

- Confirm the Lemonade Server STT entity is available.
- Run one transcription path.
- Confirm text is returned.

If Lemonade does not advertise an STT model:

- Confirm the STT entity is unavailable without breaking integration setup.
- Confirm the unavailable state is understandable from the UI or logs.

## Release step

After the smoke passes:

```bash
git tag v0.2.14-beta.1
git push origin main
git push origin v0.2.14-beta.1
```

Tags containing `-alpha`, `-beta`, or `-rc` are published as GitHub pre-releases by the release workflow.
