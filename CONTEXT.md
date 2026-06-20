# Lemonade Home Assistant

The Lemonade Home Assistant context describes how a Lemonade Server is exposed through Home Assistant surfaces such as Assist, AI tasks, media generation, speech, and direct services.

## Language

**Server Entry**:
A configured Lemonade Server connection in Home Assistant. It represents shared server access and integration-wide defaults, not an assistant.
_Avoid_: Default profile, default assistant

**Model Selector**:
An entry-level model preference for a non-profile Lemonade capability such as image generation, text-to-speech, or speech-to-text. It is a fallback preference, not a user-facing assistant or AI task.
_Avoid_: Profile, assistant setting, AI task setting

**Conversation Profile**:
A user-created Lemonade assistant for Assist or voice pipelines, with its own model choice, optional prompt, and optional Home Assistant control access.
_Avoid_: Default profile, server entry

**AI Task Profile**:
A user-created Lemonade AI task target with its own data-generation model choice and optional prompt.
_Avoid_: Default profile, server entry
