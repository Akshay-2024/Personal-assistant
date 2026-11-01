
import json
import queue
from pathlib import Path

import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(-1)

MODEL_PATH = (
    Path(__file__).parent
    / "models"
    / "vosk-model-small-en-us-0.15"
)

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Vosk model not found: {MODEL_PATH}"
    )

audio_queue = queue.Queue()

model = Model(str(MODEL_PATH))
recognizer = KaldiRecognizer(model, 16000)

def audio_callback(indata, frames, time_info, status):
    if status:
        print("Audio status:", status)

    audio_queue.put(bytes(indata))

print("Vosk is ready.")
print("Speak in English. Press Ctrl+C to stop.")

try:
    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback,
    ):
        while True:
            audio_data = audio_queue.get()

            if recognizer.AcceptWaveform(audio_data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")

                if text:
                    print("YOU:", text)
            else:
                partial = json.loads(
                    recognizer.PartialResult()
                ).get("partial", "")

                if partial:
                    print("Listening:", partial, end="\r")

except KeyboardInterrupt:
    print("\nSpeech recognition stopped.")
