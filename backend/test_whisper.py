import time
from faster_whisper import WhisperModel

print("Loading Whisper medium.en model...")

start = time.time()

model = WhisperModel(
    "medium.en",
    device="cpu",
    compute_type="int8",
    download_root="models/whisper"
)

print(f"Model loading time: {time.time() - start:.2f} seconds")

print("Transcribing your recording...")

start = time.time()

segments, info = model.transcribe(
    "whisper_test.wav",
    language="en",
    beam_size=5,
    vad_filter=True
)

segments = list(segments)

print("\nRecognized speech:")

for segment in segments:
    print(segment.text.strip())

print(f"\nTranscription time: {time.time() - start:.2f} seconds")
print("Medium model test completed.")