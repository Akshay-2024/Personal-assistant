
"use client";

import { useEffect, useRef, useState } from "react";

type Message = {
  role: "assistant" | "user";
  text: string;
};

const API_URL = "http://127.0.0.1:8000";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      text: "Hello! I am JARVIS. Click the microphone or type a message to begin.",
    },
  ]);

  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [busy, setBusy] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [status, setStatus] = useState("Systems online");
  const [liveTranscript, setLiveTranscript] = useState("");

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const busyRef = useRef(false);
  const listeningRef = useRef(false);
  const voiceEnabledRef = useRef(true);
  const mountedRef = useRef(false);

  
function speak(text: string) {
  if (
    !voiceEnabledRef.current ||
    typeof window === "undefined" ||
    !("speechSynthesis" in window)
  ) {
    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  const voices = window.speechSynthesis.getVoices();

  const preferredVoice =
    voices.find(
      (voice) => voice.lang.toLowerCase() === "en-in"
    ) ||
    voices.find(
      (voice) =>
        voice.lang.toLowerCase().startsWith("en") &&
        /natural|neural/i.test(voice.name)
    ) ||
    voices.find((voice) =>
      voice.lang.toLowerCase().startsWith("en")
    );

  if (preferredVoice) {
    utterance.voice = preferredVoice;
    utterance.lang = preferredVoice.lang;
  } else {
    utterance.lang = "en-IN";
  }

  utterance.rate = 0.96;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  window.speechSynthesis.speak(utterance);
}


  async function sendMessage(text: string) {
    const message = text.trim();

    if (!message || busyRef.current) return;

    busyRef.current = true;
    setBusy(true);
    setInput("");
    setStatus("JARVIS is thinking...");

    setMessages((previous) => [
      ...previous,
      { role: "user", text: message },
    ]);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "The AI service could not process your request."
        );
      }

      const reply = String(data.reply ?? "").trim();

      if (!reply) {
        throw new Error("JARVIS received an empty response.");
      }

      setMessages((previous) => [
        ...previous,
        { role: "assistant", text: reply },
      ]);

      setStatus("Response received");
      speak(reply);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: `Sorry, I couldn't complete that request. ${errorMessage}`,
        },
      ]);

      setStatus("Connection or service error");
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }

  async function startListening() {
    if (busyRef.current || listeningRef.current) {
      return;
    }
    window.speechSynthesis.cancel();  
    try {
      setLiveTranscript("");
      setStatus("Starting offline voice recognition...");

      const response = await fetch(`${API_URL}/listen/start`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Could not start listening.");
      }

      listeningRef.current = true;
      setListening(true);
      setStatus("Listening offline... Speak now.");

      pollRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(
            `${API_URL}/listen/status`
          );

          if (!statusResponse.ok) {
            throw new Error("Unable to read listening status.");
          }

          const statusData = await statusResponse.json();

          if (statusData.error) {
            setStatus(`Speech recognition error: ${statusData.error}`);
            return;
          }

          const transcript = String(
            statusData.partial || statusData.transcript || ""
          );

          setLiveTranscript(transcript);
        } catch {
          setStatus("Unable to read Vosk transcription.");
        }
      }, 300);
    } catch (error) {
      listeningRef.current = false;
      setListening(false);

      setStatus(
        error instanceof Error
          ? error.message
          : "Unable to start offline voice recognition."
      );
    }
  }

  async function stopListening() {
    if (!listeningRef.current) return;

    listeningRef.current = false;
    setListening(false);
    setStatus("Finishing transcription...");

    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }

    try {
      const response = await fetch(`${API_URL}/listen/stop`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Could not stop listening.");
      }

      if (data.error) {
        throw new Error(data.error);
      }

      const transcript = String(data.transcript || "").trim();

      setLiveTranscript(transcript);

      if (transcript) {
        await sendMessage(transcript);
      } else {
        setStatus("No speech detected. Please try again.");
      }
    } catch (error) {
      setStatus(
        error instanceof Error
          ? error.message
          : "Unable to finish speech recognition."
      );
    }
  }

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;

      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }

      // Best-effort cleanup if the page is closed while listening.
      void fetch(`${API_URL}/listen/stop`, {
        method: "POST",
        keepalive: true,
      }).catch(() => {});

      window.speechSynthesis?.cancel();
    };
  }, []);

  return (
    <main className="jarvis-page">
      <section className="jarvis-panel">
        <header className="jarvis-header">
          <div>
            <p className="eyebrow">PERSONAL AI SYSTEM</p>
            <h1>J.A.R.V.I.S.</h1>
            <p className="subtitle">
              Just A Rather Very Intelligent System
            </p>
          </div>

          <span className="online-indicator">
            <span className="online-dot" />
            ONLINE
          </span>
        </header>

        <div className="voice-orb" aria-label="JARVIS voice interface">
          <div className={`orb-core ${listening ? "orb-listening" : ""}`}>
            <span>{listening ? "●" : "J"}</span>
          </div>
        </div>

        <p className="system-status" aria-live="polite">
          {status}
        </p>

        {listening && (
          <p className="live-transcript" aria-live="polite">
            {liveTranscript || "Listening for your voice..."}
          </p>
        )}

        <div className="voice-controls">
          <button
            className={`mic-button ${listening ? "mic-active" : ""}`}
            onClick={() => {
              if (listening) {
                void stopListening();
              } else {
                void startListening();
              }
            }}
            disabled={busy}
          >
            {listening ? "■ Stop listening" : "🎙 Start speaking"}
          </button>

          <button
            className="secondary-button"
            onClick={() => {
              const enabled = !voiceEnabled;
              voiceEnabledRef.current = enabled;
              setVoiceEnabled(enabled);

              if (!enabled) {
                window.speechSynthesis?.cancel();
              }
            }}
          >
            {voiceEnabled ? "🔊 Voice on" : "🔇 Voice off"}
          </button>
        </div>

        <div className="message-list" aria-live="polite">
          {messages.map((message, index) => (
            <article
              key={`${index}-${message.role}`}
              className={`message ${message.role}`}
            >
              <span className="message-role">
                {message.role === "user" ? "YOU" : "JARVIS"}
              </span>
              <p>{message.text}</p>
            </article>
          ))}

          {busy && <p className="thinking">JARVIS is processing...</p>}
        </div>

        <form
          className="chat-form"
          onSubmit={(event) => {
            event.preventDefault();
            void sendMessage(input);
          }}
        >
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Type a message to JARVIS..."
            aria-label="Message to JARVIS"
            disabled={busy || listening}
          />

          <button
            type="submit"
            disabled={busy || listening || !input.trim()}
          >
            Send
          </button>
        </form>

        <footer className="jarvis-footer">
          VOSK OFFLINE STT · GEMINI AI · LOCAL FRONTEND
        </footer>
      </section>
    </main>
  );
}
