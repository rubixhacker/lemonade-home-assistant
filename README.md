# Lemonade Server Home Assistant custom integration

This repository packages the Lemonade Server Home Assistant custom integration for manual installs and HACS custom repository installs.

## HACS install

Until this integration is ready for Home Assistant core review, install it through HACS as a custom repository:

Use this direct HACS link:

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rubixhacker&repository=lemonade-home-assistant&category=integration)

Or add it manually:

1. In Home Assistant, open HACS.
2. Open **Custom repositories**.
3. Add this GitHub repository URL.
4. Select **Integration** as the category.
5. Install **Lemonade Server**.
6. Restart Home Assistant.
7. Go to **Settings -> Devices & services -> Add integration -> Lemonade Server**.

HACS installs from GitHub releases. Each release tag contains the integration at:

```text
custom_components/lemonade/
```

You can still build the release asset locally for manual inspection with:

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

The release workflow verifies the HACS package shape and publishes release notes. Tags containing `-alpha`, `-beta`, or `-rc` are published as pre-releases; plain version tags are published as stable releases.

## Manual install

Copy the `custom_components/lemonade` directory from this repository to:

```text
/config/custom_components/lemonade/
```

Then restart Home Assistant and add the integration from the UI.

## Assist and AI tasks

After installing the integration, create a profile before using Lemonade with Assist or AI tasks:

1. Open **Settings -> Devices & services -> Lemonade Server**.
2. Pick **Default model** from the Lemonade model dropdown if one omni model should back every Lemonade feature.
3. Use **Add service** or the `+` buttons in the entry details.
4. Add a **Conversation profile** for Assist.
5. Add an **AI task profile** for AI task entities.

See [custom_components/lemonade/README.md](custom_components/lemonade/README.md) for setup details and reverse-proxy notes.

## Features

- Sensors for server status and model counts.
- Select entities for default conversation, AI task, image, TTS, and STT models.
- Conversation agents through conversation profile subentries.
- AI task profile entities with data and image generation support.
- TTS provider support.
- STT provider support.
- Direct services for chat completion, image generation, transcription, and text-to-speech.

See [custom_components/lemonade/README.md](custom_components/lemonade/README.md) for integration usage details.
