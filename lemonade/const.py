"""Constants for the Lemonade Server integration."""

from homeassistant.const import Platform

DOMAIN = "lemonade"
DEFAULT_NAME = "Lemonade Server"
DEFAULT_URL = "http://localhost:13305"
DEFAULT_TIMEOUT = 30.0
DEFAULT_SCAN_INTERVAL_SECONDS = 60
DEFAULT_MODEL = "lemonade-omni"

CONF_TIMEOUT = "timeout"
CONF_ENTRY_ID = "entry_id"
CONF_DEFAULT_CONVERSATION_MODEL = "default_conversation_model"
CONF_DEFAULT_AI_TASK_MODEL = "default_ai_task_model"
CONF_DEFAULT_IMAGE_MODEL = "default_image_model"
CONF_DEFAULT_TTS_MODEL = "default_tts_model"
CONF_DEFAULT_STT_MODEL = "default_stt_model"
CONF_LLM_HASS_API = "llm_hass_api"

SUBENTRY_TYPE_CONVERSATION = "conversation"
SUBENTRY_TYPE_AI_TASK = "ai_task_data"

CAPABILITY_CONVERSATION = "conversation"
CAPABILITY_AI_TASK = "ai_task"
CAPABILITY_TOOL_CALLING = "tool_calling"
CAPABILITY_VISION = "vision"
CAPABILITY_IMAGE = "image"
CAPABILITY_IMAGE_EDIT = "image_edit"
CAPABILITY_TTS = "tts"
CAPABILITY_STT = "stt"
CAPABILITY_EMBEDDINGS = "embeddings"
CAPABILITIES = (
    CAPABILITY_CONVERSATION,
    CAPABILITY_AI_TASK,
    CAPABILITY_TOOL_CALLING,
    CAPABILITY_VISION,
    CAPABILITY_IMAGE,
    CAPABILITY_IMAGE_EDIT,
    CAPABILITY_TTS,
    CAPABILITY_STT,
    CAPABILITY_EMBEDDINGS,
)
MODEL_OPTION_BY_CAPABILITY = {
    CAPABILITY_CONVERSATION: CONF_DEFAULT_CONVERSATION_MODEL,
    CAPABILITY_AI_TASK: CONF_DEFAULT_AI_TASK_MODEL,
    CAPABILITY_IMAGE: CONF_DEFAULT_IMAGE_MODEL,
    CAPABILITY_TTS: CONF_DEFAULT_TTS_MODEL,
    CAPABILITY_STT: CONF_DEFAULT_STT_MODEL,
}

SERVICE_CHAT_COMPLETION = "chat_completion"
SERVICE_GENERATE_IMAGE = "generate_image"
SERVICE_TRANSCRIBE_AUDIO = "transcribe_audio"
SERVICE_TEXT_TO_SPEECH = "text_to_speech"

ATTR_MESSAGES = "messages"
ATTR_PROMPT = "prompt"
ATTR_SYSTEM_PROMPT = "system_prompt"
ATTR_TEXT = "text"
ATTR_FILE_PATH = "file_path"
ATTR_LANGUAGE = "language"
ATTR_VOICE = "voice"
ATTR_RESPONSE_FORMAT = "response_format"
ATTR_TEMPERATURE = "temperature"
ATTR_MAX_TOKENS = "max_tokens"
ATTR_SIZE = "size"
ATTR_SAVE = "save"
ATTR_FILENAME = "filename"
ATTR_MEDIA_PATH = "media_path"
ATTR_ATTACHMENTS = "attachments"
ATTR_STRUCTURE = "structure"

ENDPOINT_HEALTH = "/v1/health"
ENDPOINT_MODELS = "/v1/models"
ENDPOINT_CHAT = "/v1/chat/completions"
ENDPOINT_IMAGES_GENERATIONS = "/v1/images/generations"
ENDPOINT_AUDIO_TRANSCRIPTIONS = "/v1/audio/transcriptions"
ENDPOINT_AUDIO_SPEECH = "/v1/audio/speech"

PLATFORMS = (
    Platform.SENSOR,
    Platform.SELECT,
    Platform.CONVERSATION,
    Platform.AI_TASK,
    Platform.TTS,
    Platform.STT,
)
