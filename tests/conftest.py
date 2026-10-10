"""Test configuration: keep the suite offline, fast and deterministic."""
import os

# Must run before test modules import the app, because the app builds its Pipeline at import time.
os.environ["USE_LLM"] = "false"
for _name in ("FOUNDRY_ENDPOINT", "FOUNDRY_MODEL", "GITHUB_MODELS_TOKEN"):
    os.environ.pop(_name, None)

try:
    import dotenv

    dotenv.load_dotenv = lambda *args, **kwargs: False  # tests never read a developer's .env
except ImportError:
    pass