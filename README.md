# Lemonade Server Home Assistant custom integration

This repository packages the Lemonade Server Home Assistant custom integration for manual installs and HACS custom repository installs.

## HACS install

Until this integration is ready for Home Assistant core review, install it through HACS as a custom repository:

1. In Home Assistant, open HACS.
2. Open **Custom repositories**.
3. Add this GitHub repository URL.
4. Select **Integration** as the category.
5. Install **Lemonade Server**.
6. Restart Home Assistant.
7. Go to **Settings -> Devices & services -> Add integration -> Lemonade Server**.

HACS installs from GitHub releases. Each release must include a `lemonade.zip` asset containing the integration at:

```text
custom_components/lemonade/
```

Build the release asset with:

```bash
scripts/build-hacs-release.sh
```

The generated asset is written to `dist/lemonade.zip`.

## Release

Create a version tag and push it:

```bash
git tag v0.2.1
git push origin v0.2.1
```

Testing tags are marked as GitHub pre-releases:

```bash
git tag v0.2.1-beta.1
git push origin v0.2.1-beta.1
```

The release workflow builds `dist/lemonade.zip` and publishes it as the HACS release asset. Tags containing `-alpha`, `-beta`, or `-rc` are published as pre-releases; plain version tags are published as stable releases.

## Manual install

Copy the `lemonade` directory from this repository to:

```text
/config/custom_components/lemonade/
```

Then restart Home Assistant and add the integration from the UI.

## Features

- Sensors for server status and model counts.
- Select entities for default conversation, AI task, image, TTS, and STT models.
- Conversation agents through conversation profile subentries.
- AI task profile entities with data and image generation support.
- TTS provider support.
- STT provider support.
- Direct services for chat completion, image generation, transcription, and text-to-speech.

See [lemonade/README.md](lemonade/README.md) for integration usage details.
