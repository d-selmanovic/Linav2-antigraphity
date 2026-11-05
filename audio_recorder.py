import os
import time
import wave
import logging
from typing import Optional, List, Dict

import numpy as np

logger = logging.getLogger("CallRecorder")


class CallRecorder:
    """
    Zeichnet Anrufe in WAV-Dateien auf (Caller + Agent) und speichert Gesprächstranskripte.
    """

    def __init__(
        self,
        call_id: str,
        caller_id: str,
        sample_rate: int = 8000,
        output_dir: str = "recordings",
        enabled: bool = True
    ):
        self.call_id = call_id
        self.caller_id = caller_id or "unbekannt"
        self.sample_rate = sample_rate
        self.output_dir = output_dir
        self.enabled = enabled
        self.start_time = time.time()
        self.transcript: List[Dict[str, str]] = []

        # Puffer für Audio-Frames
        self.caller_frames: List[bytes] = []
        self.agent_frames: List[bytes] = []

        if self.enabled:
            os.makedirs(self.output_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            safe_caller = "".join(c for c in self.caller_id if c.isalnum() or c in "+_")
            self.filename_base = f"call_{timestamp}_{safe_caller}_{self.call_id[:8]}"
            self.wav_path = os.path.join(self.output_dir, f"{self.filename_base}.wav")
            self.transcript_path = os.path.join(self.output_dir, f"{self.filename_base}_transcript.txt")
        else:
            self.wav_path = None
            self.transcript_path = None

    def record_caller_audio(self, audio_bytes: bytes):
        """Puffert Audio-Frames des Anrufers (in PBX Sample Rate)"""
        if self.enabled and audio_bytes:
            self.caller_frames.append(audio_bytes)

    def record_agent_audio(self, audio_bytes: bytes):
        """Puffert Audio-Frames von Lina (in PBX Sample Rate)"""
        if self.enabled and audio_bytes:
            self.agent_frames.append(audio_bytes)

    def add_transcript_entry(self, speaker: str, text: str):
        """Fügt einen Transkript-Eintrag hinzu (speaker: 'caller' oder 'lina')"""
        if text and text.strip():
            self.transcript.append({
                "timestamp": round(time.time() - self.start_time, 2),
                "speaker": speaker,
                "text": text.strip()
            })

    def finalize(self) -> Optional[str]:
        """
        Schreibt die WAV-Datei und das Text-Transkript auf Festplatte.
        Gibt den Pfad der WAV-Datei zurück.
        """
        if not self.enabled:
            return None

        try:
            # 1. Erstelle kombiniertes Mono-Audio (oder Stereo)
            caller_raw = b"".join(self.caller_frames)
            agent_raw = b"".join(self.agent_frames)

            max_len = max(len(caller_raw), len(agent_raw))
            if max_len == 0:
                logger.info(f"Keine Audiodaten für Anruf {self.call_id} empfangen.")
                return None

            # Auffüllen auf gleiche Länge
            caller_arr = np.frombuffer(caller_raw.ljust(max_len, b"\x00"), dtype=np.int16)
            agent_arr = np.frombuffer(agent_raw.ljust(max_len, b"\x00"), dtype=np.int16)

            # Mono-Mix mit Clipping-Schutz: (Caller + Lina) / 2
            mixed = np.clip((caller_arr.astype(np.int32) + agent_arr.astype(np.int32)) // 2, -32768, 32767).astype(np.int16)

            # 2. Schreibe WAV-Datei
            with wave.open(self.wav_path, "wb") as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-Bit PCM
                wf.setframerate(self.sample_rate)
                wf.writeframes(mixed.tobytes())

            duration = round(time.time() - self.start_time, 1)
            logger.info(f"💾 Anrufaufzeichnung gespeichert: {self.wav_path} ({duration}s)")

            # 3. Schreibe Transkript-Datei
            if self.transcript:
                with open(self.transcript_path, "w", encoding="utf-8") as tf:
                    tf.write(f"Gesprächstranskript — Anruf {self.call_id}\n")
                    tf.write(f"Anrufer: {self.caller_id} | Dauer: {duration}s\n")
                    tf.write("=" * 60 + "\n\n")
                    for entry in self.transcript:
                        speaker_label = "Lina (Job-Step)" if entry["speaker"] == "lina" else f"Anrufer ({self.caller_id})"
                        tf.write(f"[{entry['timestamp']}s] {speaker_label}:\n  {entry['text']}\n\n")
                logger.info(f"📝 Transkript gespeichert: {self.transcript_path}")

            return self.wav_path

        except Exception as e:
            logger.error(f"Fehler beim Speichern der Anrufaufzeichnung: {e}")
            return None
