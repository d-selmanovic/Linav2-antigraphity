---
name: lina-voice-agent
description: >
  Operational setup, configuration, troubleshooting, and production deployment guide for the Lina AI Voice Agent
  (Gemini 3.8 Live, FreeSWITCH PBX, direct Airtable integration, Call Recording, Langfuse Tracing, MCP, n8n). Use whenever configuring, auditing,
  populating missing API keys, deploying, or debugging the Lina Voice Agent codebase in Antigravity, Gemini,
  Claude Code, or Codex.
license: Apache-2.0
metadata:
  version: 2.1.0
  author: Step2Job / Job-Step
  system: gemini-3.8-live-pbx
---

# Lina AI Voice Agent — Operations & Deployment Skill

Use this skill whenever an AI assistant (Antigravity, Gemini, Claude Code, OpenAI Codex, Cursor) is tasked with setting up, checking, updating, troubleshooting, or deploying the **Lina Voice Agent** for Job-Step / Step2Job recruiting.

---

## 1. System Overview & Architecture

Lina is a full-duplex conversational voice agent designed for recruiting construction workers in Bosnia and Herzegovina (Bihać casting 16–20.11., German construction contracts with €4.752 – €5.192 gross salary).

```
[ FreeSWITCH PBX ] (G.711 PCM, 8kHz)
       │  WebSocket (ws://<IPv4>:8000/ws/pbx?caller_id=${caller_id_number})
       ▼
[ FastAPI server.py ] 
       │  • Resamples 8kHz PBX ↔ 16kHz/24kHz Gemini
       │  • Manages bidirectional WebSocket session
       │  • Writes Audio Recording (.wav) & Transcripts (.txt) via audio_recorder.py
       │  • Telemetry & Tracing via Langfuse (telemetry.py)
       ├───▶ [ Google Gemini 3.8 Live API ] (models/gemini-3.8-live)
       │         • Audio in / Audio out
       │         • Native Real-Time Transcription (Caller + Lina)
       │         • Bosnian ijekavski prompt with audio-steering
       │         • Function calling: `sacuvaj_kandidata_u_airtable`
       ▼
[ Tool Execution & Integrations ]
       ├───▶ [ Airtable direct client: airtable_service.py ] ──▶ Table: "Prijave (test)"
       ├───▶ [ Langfuse Observability: telemetry.py ] ────────▶ Cloud / Self-hosted Traces
       ├───▶ [ MCP Bridge: mcp_bridge.py ] (Extensible plugins)
       └───▶ [ Optional n8n Webhook ] (Post-call alerts)
```

---

## 2. Codebase Map & File Responsibilities

| File | Purpose | Critical Code Locations |
| :--- | :--- | :--- |
| `server.py` | FastAPI server, WebSocket endpoint `/ws/pbx`, audio resampling, Gemini Live session management, tool dispatching, transcription events, Langfuse spans. | Lines 50–120 (audio resampler), 140–280 (Gemini Live loop) |
| `audio_recorder.py` | Dual-side call audio recorder (mixed WAV output) and timestamped dialogue transcription exporter (`./recordings/*.wav`, `*_transcript.txt`). | `CallRecorder.record_caller_audio()`, `record_agent_audio()`, `finalize()` |
| `telemetry.py` | Langfuse LLM Observability & Tracing client. Manages call sessions, tool execution spans, error levels, and latency monitoring. | `LinaTracer.start_call_trace()`, `DummyTrace` fallback |
| `logger_config.py` | Structured rotating file logging (`logs/lina.log`, `logs/error.log`) and live in-memory telemetry metrics. | `setup_logging()`, `metrics.record_call_start()` |
| `commit_and_deploy.sh` | 7-step pre-push integrity auditor, skill synchronizer, and GitHub deployer. | Terminal execution |
| `airtable_service.py` | Async Airtable integration with telephone normalization (`+387 / 0`), candidate upsert into `Prijave (test)`. | Schema mapping dictionary, `save_or_update_candidate()` |
| `prompts.py` | Bosnian ijekavski system prompt, objection handling (salary, robot counter, casting dates), Gemini tool schema declarations. | `LINA_SYSTEM_INSTRUCTION`, `AIRTABLE_TOOL_DECLARATION` |
| `mcp_bridge.py` | Dynamic Model Context Protocol client for extending Lina with external tools. | `MCPBridge.execute_tool()` |
| `setup_skills.sh` | 1-click executable installer registering the skill globally across Antigravity, Claude Code, and Codex. | Terminal execution |
| `AGENTS.md` & `CLAUDE.md`| Standardized assistant steering files for OpenAI Codex and Claude Code. | Repo root |
| `test_local.py` | CLI test suite using local microphone/speaker to test speech, Airtable upsert, and n8n webhook. | Terminal interactive test |
| `Dockerfile` | Multi-stage production container setup with Python 3.11-slim, libasound2/portaudio, and langfuse. | Production container build |
| `docker-compose.yml` | Container orchestration with port 8000 exposed, environment variable loading, and automatic restart. | `docker compose up -d` |
| `.env.example` | Template for required API keys, network host/port, recording, and Langfuse configurations. | Reference for all keys |
| `GESAMTDOKUMENTATION.md` | Master documentation consolidating all operational, architectural, and business steps. | Reference manual |
| `ANLEITUNG.md` | Step-by-step FreeSWITCH dialplan and deployment setup guide. | PBX integration |
| `HR_OPERATIVER_PROZESS.md`| Post-call HR workflow: SMS confirmations, WhatsApp document collection, recruiter alerts. | Downstream pipeline |
| `VOICE_BRANDING_GUIDE.md`| Voice design and voice cloning instructions using Gemini 3.8 Flash TTS. | Voice branding |

---

## 3. Configuration Pre-Flight Checklist (`.env`)

Whenever an agent is asked to check or fix the configuration, inspect `/Users/Agents/Lina JSI Gemini/.env`. If missing, copy from `.env.example`:

```bash
cp .env.example .env
```

### Required & Optional Configuration Keys

| Variable | Required? | Description & Where to Obtain | Example / Format |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | **Ja** | Google AI Studio API Key. Obtain from [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey). | `AIzaSy...` (39 Zeichen) |
| `AIRTABLE_API_KEY` | **Ja** | Airtable Personal Access Token (PAT). Create at [airtable.com/create/tokens](https://airtable.com/create/tokens). Scopes: `data.records:read`, `data.records:write`, `schema.bases:read`. | `pat...` (~50 Zeichen) |
| `AIRTABLE_BASE_ID` | **Ja** | The Airtable Base ID from the URL: `https://airtable.com/appXXXXX/...`. | `appXXXXXXXXXXXXXX` |
| `AIRTABLE_TABLE_NAME` | **Ja** | The exact table name. Default: `Prijave (test)`. | `Prijave (test)` |
| `HOST` | **Ja** | Bind IP. Use `0.0.0.0` so FreeSWITCH PBX can connect via server IPv4. | `0.0.0.0` |
| `PORT` | **Ja** | Listening port. Default: `8000`. | `8000` |
| `PBX_SAMPLE_RATE` | **Ja** | Sample rate of PBX audio stream. Default is `8000` (G.711). Use `16000` for G.722 HD-Voice. | `8000` |
| `VOICE_NAME` | **Ja** | Gemini voice name. Options: `Aoede`, `Kore`, `Puck`, `Fenrir`, or custom replication ID. | `Aoede` |
| `ENABLE_CALL_RECORDING`| Nein | Speichert Anrufe als WAV und TXT-Transkripte. Default: `true`. | `true` |
| `RECORDINGS_DIR` | Nein | Zielverzeichnis für Aufnahmen. Default: `recordings`. | `recordings` |
| `LOGS_DIR` | Nein | Zielverzeichnis für Logs & Error-Logs. Default: `logs`. | `logs` |
| `DEBUG_MODE` | Nein | Verboses Frame- & Audio-Tracing. Default: `false`. | `false` |
| `LANGFUSE_PUBLIC_KEY` | Nein | Langfuse Tracing Public Key. Aus [cloud.langfuse.com](https://cloud.langfuse.com). | `pk-lf-...` |
| `LANGFUSE_SECRET_KEY` | Nein | Langfuse Tracing Secret Key. | `sk-lf-...` |
| `LANGFUSE_HOST` | Nein | Langfuse Server Host. Default: `https://cloud.langfuse.com`. | `https://cloud.langfuse.com` |
| `N8N_WEBHOOK_URL` | Nein | Optionaler n8n Webhook URL. | `http://<n8n-ip>:5678/webhook/lina` |

---

## 4. Wie Transkription & Aufnahme funktionieren

### A. Live-Transkription (Speech-to-Text)
Lina nutzt die **native Streaming-Transkription** von Google Gemini 3.8 Live über:
```python
input_audio_transcription=types.AudioTranscriptionConfig(),
output_audio_transcription=types.AudioTranscriptionConfig()
```
* **Anrufer:** Gemini liefert synchron zum Sprachstrom den erkannten Text in `server_content.input_transcription.text`.
* **Lina:** Die gesprochenen Antworten werden parallel in `server_content.output_transcription.text` bereitgestellt.
* **Vorteil:** Kein externer STT-Dienst (Whisper/Deepgram) nötig — 0 zusätzliche Latenz, keine Zusatzkosten.

### B. Anruf-Aufzeichnung (Call Recording)
1. **Server-seitig (`audio_recorder.py`):**
   * Zeichnet Caller-Frames und Lina-Frames auf.
   * Speichert bei Gesprächsende eine saubere WAV-Datei in `./recordings/call_{TIMESTAMP}_{CALLER_ID}.wav`.
   * Exportiert ein zeitgestempeltes Text-Transkript in `./recordings/call_{TIMESTAMP}_{CALLER_ID}_transcript.txt`.
2. **PBX-seitig (FreeSWITCH):**
   * Im FreeSWITCH-Dialplan kann mit einer einzigen Zeile die native PBX-Aufnahme aktiviert werden:
     ```xml
     <action application="record_session" data="/var/lib/freeswitch/recordings/${uuid}.wav"/>
     ```

### C. Langfuse LLM Observability & Tracing (`telemetry.py`)
Wenn `LANGFUSE_PUBLIC_KEY` und `LANGFUSE_SECRET_KEY` in `.env` hinterlegt sind:
* Jeder Anruf startet einen Langfuse Trace mit `session_id`, `caller_id` und Kampagnen-Tags.
* Jeder Redebeitrag (`caller_speech`, `lina_speech`) wird als Event getrackt.
* Jeder Datenbank-Aufruf (`sacuvaj_kandidata_u_airtable`) erzeugt einen Span mit Parametern, Latenz und Rückgabewert.
* Fehlen die Keys, schaltet das System automatisch in den Dummy-Modus ohne Fehlermeldungen.

---

## 5. FreeSWITCH PBX Integration

In FreeSWITCH (`/etc/freeswitch/dialplan/default/`):

```xml
<extension name="Lina_Recruiting_Agent">
  <condition field="destination_number" expression="^.*$">
    <!-- 1. Kanal annehmen -->
    <action application="answer"/>
    <!-- 2. Optionale native PBX-Aufnahme -->
    <action application="record_session" data="/var/lib/freeswitch/recordings/${uuid}.wav"/>
    <!-- 3. Kurze Stille zur Stabilisierung des RTP-Puffers -->
    <action application="playback" data="silence_stream://500"/>
    <!-- 4. Duplex Audio-Stream an Lina via IPv4 -->
    <action application="audio_stream" data="start ws://<SERVER_IPV4>:8000/ws/pbx?caller_id=${caller_id_number}"/>
  </condition>
</extension>
```

---

## 6. How to Test and Run the Agent

### Health & Monitoring Endpoints
```bash
# 1. Quick Health Check:
curl http://localhost:8000/health

# 2. Live Telemetrie & Betriebsmetriken (Uptime, Calls, Tools):
curl http://localhost:8000/metrics

# 3. Fehlerpuffer (letzte aufgetretene Exceptions):
curl http://localhost:8000/debug/errors
```

Erwartete Health JSON-Antwort:
```json
{
  "status": "healthy",
  "agent": "Lina (Job-Step)",
  "model": "models/gemini-3.8-live",
  "voice": "Aoede",
  "airtable_direct": true,
  "mcp_enabled": true,
  "call_recording_enabled": true,
  "langfuse_tracing_enabled": true,
  "active_calls": 0,
  "total_calls": 12,
  "total_errors": 0
}
```

### 7-Schritte Pre-Push Integrity Check & Deploy
Führen Sie vor Änderungen immer aus:
```bash
./commit_and_deploy.sh "Ihre Commit-Nachricht"
```

### Lokaler Mikrofon-Test
```bash
python test_local.py
```

### Production Deployment mit Docker Compose
```bash
docker compose up -d --build
docker compose logs -f
```
docker compose logs -f
```
