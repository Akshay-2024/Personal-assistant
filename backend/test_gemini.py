
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).with_name(".env"))

keys = [
    key.strip()
    for key in os.getenv(
        "GEMINI_API_KEYS",
        os.getenv("GEMINI_API_KEY", ""),
    ).split(",")
    if key.strip()
]

if len(keys) < 2:
    raise SystemExit("Key #2 was not found in backend/.env")

client = genai.Client(
    api_key=keys[1],
    http_options=types.HttpOptions(timeout=180000),
)

try:
    print("Testing key #2 with gemini-3.8-flash...")
    
    response = client.interactions.create(
        model="gemini-3.8-flash",
        input="Reply with exactly: JARVIS online",
        generation_config={
            "max_output_tokens": 64,
            "thinking_level": "low",
        },
    )

    print("SUCCESS:", response.output_text)

except Exception as exc:
    print("FAILED:", type(exc).__name__)
    print("Reason:", str(exc))
