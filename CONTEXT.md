# Lemonade Home Assistant

The Lemonade Home Assistant context describes how a Lemonade Server is exposed through Home Assistant surfaces such as Assist, AI tasks, media generation, speech, and direct services.

## Language

**Server Entry**:
A configured Lemonade Server connection in Home Assistant. It represents shared server access and integration-wide defaults, not an assistant or a Home Assistant device.
_Avoid_: Default profile, default assistant

**Model Selector**:
An entry-level model preference for a non-profile Lemonade capability such as image generation, text-to-speech, or speech-to-text. It is a fallback preference, not a user-facing assistant or AI task.
_Avoid_: Profile, assistant setting, AI task setting

**Conversation Profile**:
A user-created Lemonade assistant for Assist or voice pipelines, with its own model choice, optional prompt, optional Home Assistant control access, chat history limit, optional model keep-alive override, and its own Home Assistant subentry device.
_Avoid_: Default profile, server entry

**AI Task Profile**:
A user-created Lemonade AI task target with its own data-generation model choice, optional prompt, chat history limit, optional model keep-alive override, and its own Home Assistant subentry device.
_Avoid_: Default profile, server entry

**Context Length**:
The model context window managed by Lemonade Server. Home Assistant profiles should not force this; they only control how many history messages are sent.
_Avoid_: Max history, message limit
