import sounddevice as sd
import soundfile as sf

DEVICE = 1
DURATION = 10
SAMPLE_RATE = 16000

print("Recording from Mivi DuoPods i7...")
audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",
    device=DEVICE
)
sd.wait()

sf.write("whisper_test.wav", audio, SAMPLE_RATE)
print("Recording saved: whisper_test.wav")
