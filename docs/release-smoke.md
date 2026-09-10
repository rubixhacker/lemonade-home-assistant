# Release smoke checklist

Use this checklist before publishing a Lemonade Server Home Assistant beta or stable release.

## Current target

- Tag: `v1.1.2`
- Manifest version: `1.1.2`
- Install source: built HACS release artifact, not a direct working-tree copy
- Lemonade source: real Lemonade Server, not a fake endpoint

## Local package checks

Run from the repository root:

```bash
python3 -m venv /tmp/lemonade-ha-e2e
/tmp/lemonade-ha-e2e/bin/pip install -r requirements-e2e.txt
/tmp/lemonade-ha-e2e/bin/pytest tests/e2e -v
python3 -m unittest tests.test_models tests.test_runtime tests.test_beacon -v
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

- End-to-end feature tests pass against real Home Assistant config flows,
  services, entities, HTTP, and UDP boundaries.
- Unit tests pass.
- Python files compile.
- JSON files validate.
- `dist/lemonade.zip` contains `custom_components/lemonade/`.
- The artifact contains `manifest.json`, `strings.json`, `translations/en.json`, and `brand/icon.png`.

## Home Assistant smoke

Install `dist/lemonade.zip` into a Home Assistant instance as the release artifact under test, then restart Home Assistant.

Use a real Lemonade Server URL reachable from Home Assistant. The server must have at least one downloaded chat-capable model. Image, TTS, and STT checks are conditional on the models Lemonade advertises through `/v1/models`.
Multilingual native TTS verification requires Lemonade Server v10.0.1 or later.

Use the 120-second request timeout for cold-model testing. A model that returns a server-side `model_load_error` may be retried once after its backend starts; a repeated error fails the smoke test.

### Required checks

- Add a Lemonade Server Entry from the UI.
- Confirm a Lemonade Server beacon can pre-fill setup when advertised.
- Confirm Endpoint Reconfiguration validates and replaces a test Server Endpoint
  without changing its profiles.
- Confirm the integration loads without startup errors.
- Confirm the integration page shows status and model-count entities.
- Confirm a new Server Entry has one Starter Conversation Profile.
- Create one Router-backed Conversation Profile with Router Metadata.
- Select the Conversation Profile in Assist or a voice pipeline.
- Send one Assist prompt and confirm a response is returned.
- Create one Omni-backed AI Task Profile.
- Run one AI task data-generation path and confirm a response is returned.
- Run `lemonade.classify_text` and confirm the Lemonade score mapping is returned
  unchanged.
- Run `lemonade.chat_completion` with `route_trace: true` and confirm its raw
  response contains a Route Decision.
- Confirm the native Lemonade TTS and STT providers advertise at least one
  non-English Home Assistant locale.
- Confirm direct service schemas are visible for:
  - `lemonade.chat_completion`
  - `lemonade.generate_image`
  - `lemonade.transcribe_audio`
  - `lemonade.text_to_speech`
  - `lemonade.classify_text`

### Conditional checks

If Lemonade advertises an image-generation model:

- Run `lemonade.generate_image` with `save: true`.
- Confirm the service response includes a `media_path`.
- Confirm the file is written under Home Assistant media storage.

If Lemonade advertises a TTS model:

- Confirm the Lemonade Server TTS entity is available.
- Generate speech through the native TTS path with an explicitly selected
  non-English locale.
- Confirm audio data is returned in that locale.

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
git tag v1.1.1
git push origin main
git push origin v1.1.1
```

Tags containing `-alpha`, `-beta`, or `-rc` are published as GitHub pre-releases by the release workflow.

## Native speech selection

Use a Lemonade Server with a downloaded Kokoro model and a known multilingual
Whisper model. These checks require a live server and playback device; the
HTTP-boundary test fixtures do not establish speech quality or device playback.

1. Select Lemonade Server text-to-speech in an Assist pipeline. Select English,
   then confirm model-labelled voice names and use Try voice to hear the result.
2. Select British English and confirm that American English voices are absent.
   Change the assistant's main Language to French, choose French speech output,
   and preview a French voice. Home Assistant filters speech languages by the
   assistant's main language.
3. Change the Server Entry's default TTS model, then repeat the saved voice
   preview. Its selected model must remain unchanged. Remove that model from
   Lemonade and try an uncached phrase: expect an error requiring a new voice,
   not a replacement model or voice.
4. Select a known multilingual Whisper model for STT and a supported assistant
   language. Speak in that language and inspect the transcription. Change to an
   English-only model and confirm unsupported languages are no longer offered.
5. On Lemonade versions before 10.0.1, confirm the TTS picker offers only the
   existing default-English-compatible language choices.

OpenMOSS saved voices require Lemonade to enable and expose its backend voice
registry. Do not mark that qualification complete by testing inline samples or
connecting Home Assistant directly to the private backend subprocess.
