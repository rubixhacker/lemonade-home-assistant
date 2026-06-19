"""Constants for the Lemonade Server integration."""

from homeassistant.const import Platform

DOMAIN = "lemonade"
DEFAULT_NAME = "Lemonade Server"
DEFAULT_URL = "http://localhost:13305"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MODEL = "lemonade-omni"

CONF_TIMEOUT = "timeout"
CONF_ENTRY_ID = "entry_id"

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

ENDPOINT_HEALTH = "/v1/health"
ENDPOINT_MODELS = "/v1/models"
ENDPOINT_CHAT = "/v1/chat/completions"
ENDPOINT_IMAGES_GENERATIONS = "/v1/images/generations"
ENDPOINT_AUDIO_TRANSCRIPTIONS = "/v1/audio/transcriptions"
ENDPOINT_AUDIO_SPEECH = "/v1/audio/speech"

PLATFORMS: tuple[Platform, ...] = ()
