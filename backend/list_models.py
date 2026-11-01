
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).with_name(".env"))
response = client.interactions.create(
    model="gemini-3.8-flash",
    input="Say hello.",
    generation_config={
        "thinking_level": "low",
        "max_output_tokens": 64,
    },
)

print("SUCCESS:", response.output_text)
keys = [
    key.strip()
    for key in os.getenv(
        "GEMINI_API_KEYS",
        os.getenv("GEMINI_API_KEY", ""),
    ).split(",")
    if key.strip()
]

if not keys:
    print("No API keys found in backend/.env")
    raise SystemExit(1)

client = genai.Client(
    api_key=keys[1] if len(keys) > 1 else keys[0],
    http_options=types.HttpOptions(timeout=180000),
)

try:
    print("Checking models available to your API key...\n")

    for model in client.models.list():
        name = getattr(model, "name", "") or ""
        supported = getattr(model, "supported_actions", []) or []

        if "generateContent" in supported:
            print(name)

except Exception as exc:
    print("Could not list models.")
    print(type(exc).__name__, str(exc))
