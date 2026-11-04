from pathlib import Path

main_file = Path(r"D:\Jarvis\backend\main.py")
source = main_file.read_text(encoding="utf-8")

old_import = "from vosk import Model, KaldiRecognizer, SetLogLevel"
new_import = """import tempfile
import wave
from faster_whisper import WhisperModel"""

start_marker = "# ---------- Offline Vosk speech recognition ----------"
end_marker = "# ---------- Chat request model ----------"

if source.count(old_import) != 1:
    raise SystemExit("STOP: Expected Vosk import was not found exactly once.")

if source.count(start_marker) != 1 or source.count(end_marker) != 1:
    raise SystemExit("STOP: Expected section markers were not found exactly once.")

start = source.index(start_marker)
end = source.index(end_marker)

if end <= start:
    raise SystemExit("STOP: Section boundaries are invalid.")

whisper_section = r'''
# ---------- Offline Whisper speech recognition ----------

WHISPER_MODEL_PATH = Path(__file__).parent / "models" / "whisper"

whisper_model = WhisperModel(
    "medium.en",
    device="cpu",
    compute_type="int8",
    download_root=str(WHISPER_MODEL_PATH),
)

MICROPHONE_DEVICE = 1  # Mivi DuoPods i7 microphone

audio_chunks = []
audio_lock = Lock()
listen_lock = Lock()
audio_stream = None

listen_state = {
    "listening": False,
    "transcript": "",
    "partial": "",
    "error": None,
}


def microphone_callback(indata, frames, time_info, status):
    if status:
        print(f"Microphone status: {status}")

    if listen_state["listening"]:
        with audio_lock:
            audio_chunks.append(bytes(indata))


# ---------- Whisper API routes ----------

@app.post("/listen/start")
def start_listening():
    global audio_stream

    with listen_lock:
        if listen_state["listening"]:
            return {"ok": True, "message": "Already listening"}

        with audio_lock:
            audio_chunks.clear()

        listen_state.update({
            "listening": False,
            "transcript": "",
            "partial": "",
            "error": None,
        })

        try:
            audio_stream = sd.RawInputStream(
                samplerate=16000,
                blocksize=4000,
                dtype="int16",
                channels=1,
                device=MICROPHONE_DEVICE,
                callback=microphone_callback,
            )

            audio_stream.start()
            listen_state["listening"] = True

            return {"ok": True, "message": "Listening started"}

        except Exception as exc:
            listen_state["error"] = str(exc)
            listen_state["listening"] = False

            if audio_stream is not None:
                try:
                    audio_stream.close()
                except Exception:
                    pass

            audio_stream = None
            return {"ok": False, "error": str(exc)}


@app.get("/listen/status")
def get_listen_status():
    return {
        "listening": listen_state["listening"],
        "transcript": listen_state["transcript"],
        "partial": listen_state["partial"],
        "error": listen_state["error"],
    }


@app.post("/listen/stop")
def stop_listening():
    global audio_stream

    with listen_lock:
        if not listen_state["listening"]:
            return {
                "ok": True,
                "transcript": listen_state["transcript"],
                "error": listen_state["error"],
            }

        listen_state["listening"] = False

        stream = audio_stream
        audio_stream = None

        if stream is not None:
            try:
                stream.stop()
            except Exception:
                pass

            try:
                stream.close()
            except Exception:
                pass

        with audio_lock:
            recorded_audio = b"".join(audio_chunks)
            audio_chunks.clear()

    if not recorded_audio:
        listen_state["error"] = "No audio was recorded."
        return {
            "ok": False,
            "transcript": "",
            "error": listen_state["error"],
        }

    recording_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
            dir=str(Path(__file__).parent),
        ) as temp_file:
            recording_path = Path(temp_file.name)

        with wave.open(str(recording_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(recorded_audio)

        segments, info = whisper_model.transcribe(
            str(recording_path),
            language="en",
            beam_size=5,
            vad_filter=True,
        )

        transcript = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ).strip()

        listen_state["transcript"] = transcript
        listen_state["error"] = None

        return {
            "ok": True,
            "transcript": transcript,
            "error": None,
        }

    except Exception as exc:
        listen_state["error"] = str(exc)

        return {
            "ok": False,
            "transcript": "",
            "error": str(exc),
        }

    finally:
        if recording_path is not None:
            try:
                recording_path.unlink(missing_ok=True)
            except Exception:
                pass


'''

updated = (
    source[:start]
    + whisper_section
    + source[end:]
)

updated = updated.replace(old_import, new_import, 1)

# Write only after all validation and replacement steps succeed.
main_file.write_text(updated, encoding="utf-8")

print("SUCCESS: Vosk section replaced with Whisper medium.en.")
print("Your Gemini and memory sections were preserved.")
