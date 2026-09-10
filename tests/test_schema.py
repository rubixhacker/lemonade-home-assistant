"""Exercise schema compatibility with real dependencies outside HA test stubs."""

from pathlib import Path
import subprocess
import sys
import unittest


class SchemaCompatibilityTests(unittest.TestCase):
    def test_internal_chat_helper_is_not_an_llm_platform(self) -> None:
        component = Path(__file__).resolve().parents[1] / "custom_components/lemonade"
        self.assertFalse((component / "llm.py").exists())
        self.assertTrue((component / "chat.py").exists())

    def test_real_serializer_sentinels_produce_json_schemas(self) -> None:
        # Runtime tests install fake libraries in sys.modules. Use a fresh
        # interpreter so this regression exercises the actual converters.
        result = subprocess.run(
            [sys.executable, "-c", '''
import importlib.util
import json
import sys
try:
    import probatio
    import voluptuous as vol
    import voluptuous_openapi as legacy
except ImportError:
    sys.exit(77)
spec = importlib.util.spec_from_file_location("schema_compat", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
special = object()
schema = vol.Schema({vol.Required("name"): str, vol.Optional("target"): special})
for sentinel in (probatio.UNSUPPORTED, legacy.UNSUPPORTED):
    def serializer(value):
        if value is special:
            return {"type": "string", "enum": ["kitchen", "bedroom"]}
        return sentinel
    converted = module.convert(schema, custom_serializer=serializer)
    payload = json.loads(json.dumps({"tools": [{"parameters": converted}]}))
    parameters = payload["tools"][0]["parameters"]
    assert parameters["type"] == "object", parameters
    assert parameters["properties"]["name"]["type"] == "string", parameters
    assert parameters["properties"]["target"]["enum"] == ["kitchen", "bedroom"]
    assert parameters["required"] == ["name"], parameters
# Also cover AI task schemas without a custom serializer and older HA.
assert module.convert(vol.Schema({"answer": str}))["type"] == "object"
module.PROBATIO_UNSUPPORTED = None
assert module.convert(vol.Schema({"answer": str}), custom_serializer=lambda _: legacy.UNSUPPORTED)["type"] == "object"
''', str(Path(__file__).resolve().parents[1] / "custom_components/lemonade/schema.py")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 77:
            self.skipTest("Install probatio and voluptuous-openapi for real schema coverage")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
