# Lemonade Home Assistant

The Lemonade Home Assistant context describes how a Lemonade Server is exposed through Home Assistant surfaces such as Assist, AI tasks, media generation, speech, and direct services.

## Language

**Server Entry**:
A configured Lemonade Server connection in Home Assistant. It represents shared server access and integration-wide defaults, not an assistant or a Home Assistant device.
_Avoid_: Default profile, default assistant

**Server Beacon**:
A Lemonade Server announcement received through one of Home Assistant's enabled, directly connected network adapters, containing a hostname and advertised API URL. It identifies a possible Server Entry endpoint but does not establish a configured connection.
_Avoid_: Server Entry, discovered entry, trusted server

**Discovered Server**:
A Server Entry candidate surfaced during user-initiated setup from a structurally valid Server Beacon whose advertised address is bound to the beacon source. It remains unverified until user confirmation and connection validation.
_Avoid_: Auto-configured server, Server Entry

**Server Endpoint**:
The normalized URL that identifies a Discovered Server or Server Entry. A beacon hostname is a display label, not server identity.
_Avoid_: Server hostname, machine identity

**Endpoint Reconfiguration**:
A user-confirmed change to a Server Entry's Server Endpoint that preserves its profiles and settings. It is never inferred from a hostname or applied automatically from a Server Beacon.
_Avoid_: Automatic endpoint migration, rediscovery

**Model Selector**:
An entry-level model preference for speech capabilities such as text-to-speech or speech-to-text. It is a fallback preference, not a user-facing assistant, AI task, or image-generation setting.
_Avoid_: Profile, assistant setting, AI task setting, image setting

**Conversation Profile**:
A user-created Lemonade assistant for Assist or voice pipelines, with its own model choice, optional prompt, optional Home Assistant control access, chat history limit, optional model keep-alive override, and its own Home Assistant subentry device.
_Avoid_: Default profile, server entry

**Starter Conversation Profile**:
The initial Lemonade assistant provided to make Assist usable before a person designs a custom assistant. It begins with the Starter Prompt, inherited model selection, and no Home Assistant control access; it remains an ordinary, editable, and removable Conversation Profile.
_Avoid_: Default conversation profile, mandatory profile

**Starter Prompt**:
The repository-owned initial instructions offered to a new Starter Conversation Profile. Its initial wording derives from Home Assistant's standard conversation instructions; once saved, the prompt is ordinary profile-owned data.
_Avoid_: Ollama prompt, GUI3-optimized prompt, fine-tuned model

**AI Task Profile**:
A user-created Lemonade AI task target with its own model choice, optional prompt, chat history limit, optional model keep-alive override, and its own Home Assistant subentry device. Depending on the selected model and task, it can process images as input for data generation or generate images as output.
_Avoid_: Default profile, server entry

**Router Model**:
A server-authored Lemonade model-selection policy that Home Assistant invokes through the ordinary chat model field. It can be selected for conversations and AI task data generation, while its candidates and routing policy remain managed by Lemonade Server.
_Avoid_: Router profile, routing service, Home Assistant router

**Route Decision**:
Opt-in diagnostic data describing how a Router Model selected the model that handled a chat request. It is returned directly to the requesting automation and is not retained as Home Assistant entity state or emitted as an event.
_Avoid_: Last route sensor, routing history, route event

**Router Metadata**:
An explicit caller- or profile-supplied mapping that a Router Model may use when selecting a candidate. The integration passes it unchanged and does not add inferred Home Assistant identities, entity context, or profile details.
_Avoid_: Router context, automatic metadata, routing prompt

**Classification Model**:
A Lemonade encoder model that assigns scores to labels for supplied text. Home Assistant selects the model but does not define the meaning of its labels.
_Avoid_: Router classifier, classification profile

**Classification Result**:
The model identifier and label-score mapping returned for one text-classification request. The requesting automation owns any threshold or domain interpretation applied to those scores.
_Avoid_: Classification decision, classified state

**Omni Model**:
A Lemonade collection model that presents several component models through the ordinary chat interface. Home Assistant can select it explicitly for conversations and AI task data generation, while Lemonade Server owns component orchestration.
_Avoid_: Omni profile, multimodal router, Home Assistant model collection

**Context Length**:
The model context window managed by Lemonade Server. Home Assistant profiles should not force this; they only control how many history messages are sent.
_Avoid_: Max history, message limit

**Speech Voice**:
A selectable way for a Lemonade speech model to speak, available for one or more supported languages. A Speech Voice identifies both the model and its voice choice so that similarly named voices remain distinguishable.
_Avoid_: Conversation Profile, speech backend

**Saved Speech Voice**:
A reusable Speech Voice whose entire lifecycle belongs to Lemonade/OpenMOSS. Home Assistant selects it without owning its creation, reference samples, storage, or deletion.
_Avoid_: Home Assistant voice profile, local voice library
