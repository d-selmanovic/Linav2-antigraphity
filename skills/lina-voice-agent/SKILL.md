---
name: lina-voice-agent
description: >
  Operational setup, configuration, troubleshooting, and production deployment guide for the Lina AI Voice Agent
  (Gemini 3.8 Live, FreeSWITCH PBX, direct Airtable integration, MCP, n8n). Use whenever configuring, auditing,
  populating missing API keys, deploying, or debugging the Lina Voice Agent codebase in Antigravity, Gemini,
  Claude Code, or Codex.
license: Apache-2.0
metadata:
  version: 2.0.0
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
       ├───▶ [ Google Gemini 3.8 Live API ] (models/gemini-3.8-live)
       │         • Audio in / Audio out
       │         • Bosnian ijekavski prompt with audio-steering
       │         • Function calling: `save_candidate_application`
       ▼
[ Tool Execution ]
       ├───▶ [ Airtable direct client: airtable_service.py ] ──▶ Table: "Prijave (test)"
       ├───▶ [ MCP Bridge: mcp_bridge.py ] (Extensible plugins)
       └───▶ [ Optional n8n Webhook ] (Post-call alerts)
```

---

## 2. Codebase Map & File Responsibilities

| File | Purpose | Critical Code Locations |
| :--- | :--- | :--- |
| `server.py` | FastAPI server, WebSocket endpoint `/ws/pbx`, audio resampling, Gemini Live session management, tool dispatching. | Lines 50–120 (audio resampler), 130–280 (Gemini Live loop) |
| `airtable_service.py` | Async Airtable integration with telephone normalization (`+387 / 0`), candidate upsert into `Prijave (test)`. | Schema mapping dictionary, `save_candidate()` |
| `prompts.py` | Bosnian ijekavski system prompt, objection handling (salary, robot counter, casting dates), Gemini tool schema declarations. | `LINA_SYSTEM_PROMPT`, `LINA_TOOLS` |
| `mcp_bridge.py` | Dynamic Model Context Protocol client for extending Lina with external tools. | `MCPBridge.call_tool()` |
| `test_local.py` | CLI test suite using local microphone/speaker to test speech, Airtable upsert, and n8n webhook. | Terminal interactive test |
| `Dockerfile` | Multi-stage production container setup with Python 3.11-slim and libasound2/portaudio. | Production container build |
| `docker-compose.yml` | Container orchestration with port 8000 exposed, environment variable loading, and automatic restart. | `docker compose up -d` |
| `.env.example` | Template for required API keys, network host/port, and audio configurations. | Reference for all keys |
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

### Required Configuration Keys

| Variable | Description & Where to Obtain | Example / Expected Format |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio API Key. Obtain from [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey). | `AIzaSy...` (39 characters) |
| `AIRTABLE_API_KEY` | Airtable Personal Access Token (PAT). Create at [airtable.com/create/tokens](https://airtable.com/create/tokens). Required Scopes: `data.records:read`, `data.records:write`, `schema.bases:read`. | `pat...` (approx. 50 characters) |
| `AIRTABLE_BASE_ID` | The Airtable Base ID. Found in the URL: `https://airtable.com/appXXXXX/...`. | `appXXXXXXXXXXXXXX` |
| `AIRTABLE_TABLE_NAME` | The exact table name. Default: `Prijave (test)`. | `Prijave (test)` |
| `HOST` | Bind IP. Use `0.0.0.0` so FreeSWITCH PBX can connect via server IPv4. | `0.0.0.0` |
| `PORT` | Listening port. Default: `8000`. | `8000` |
| `PBX_SAMPLE_RATE` | Sample rate of PBX audio stream. Default is `8000` (G.711 / standard narrowband telephony). Set to `16000` only if FreeSWITCH uses G.722 / wideband. | `8000` |
| `VOICE_NAME` | Gemini voice name. Options: `Aoede` (standard female), `Kore`, `Puck`, `Fenrir`, or custom replication ID. | `Aoede` |
| `N8N_WEBHOOK_URL` | Optional n8n webhook URL triggered on candidate save. | `http://<n8n-ip>:5678/webhook/lina-call` |

---

## 4. Airtable Database Schema Verification

Airtable table `Prijave (test)` must have these exact column names and field types:

| Column Name | Field Type in Airtable | Description |
| :--- | :--- | :--- |
| `Tačan naziv škole, grad, država` | Single line text | Candidate's highest qualification & school location. |
| `KOMPANIJA` | Single line text | Fixed value: `Step2Job / Job-Step`. |
| `RADNO MJESTO` | Single line text | Target role (e.g. `Bagerista`, `Zidar`, `Građevinski radnik`). |
| `Status boravka` | Single select or Text | `BiH` (needs visa) or `EU` (direct deployment). |
| `Mjesto` | Single line text | Candidate's current city (e.g. `Bihać`, `Cazin`, `Sarajevo`). |
| `Telefon` | Phone / Text | Candidate phone number (automatically normalized to E.164, e.g. `+38761234567`). |
| `Casting termin` | Single line text | Assigned appointment (e.g. `17.11.2026 10:00h (Bihać)`). |
| `Bilješka` | Long text | Recruiter notes, experience summary, driving license classes. |

---

## 5. FreeSWITCH PBX Integration

In FreeSWITCH (`/etc/freeswitch/dialplan/default/` or `/usr/local/freeswitch/conf/dialplan/default/`), configure the XML dialplan extension:

```xml
<extension name="Lina_Recruiting_Agent">
  <condition field="destination_number" expression="^.*$">
    <!-- 1. Answer channel immediately -->
    <action application="answer"/>
    <!-- 2. Brief silence to allow audio pipeline stabilization -->
    <action application="playback" data="silence_stream://500"/>
    <!-- 3. Connect duplex audio stream via IPv4, forwarding caller number -->
    <action application="audio_stream" data="start ws://<SERVER_IPV4>:8000/ws/pbx?caller_id=${caller_id_number}"/>
  </condition>
</extension>
```

> **Important:** The `server.py` WebSocket endpoint extracts `caller_id` automatically from the query string (`?caller_id=...`). Lina uses this directly for Airtable lookup/upsert without having to ask the caller for their phone number.

---

## 6. How to Test and Run the Agent

### Step 1: Health Check (Zero-Audio Verification)
```bash
curl http://localhost:8000/health
```
Expected JSON response:
```json
{
  "status": "healthy",
  "agent": "Lina (Job-Step)",
  "model": "models/gemini-3.8-live",
  "voice": "Aoede",
  "airtable_direct": true,
  "mcp_enabled": true
}
```

### Step 2: Local Audio Test (Microphone & Speaker)
Run the local interactive test suite:
```bash
cd "/Users/Agents/Lina JSI Gemini"
python test_local.py
```
* Speak in Bosnian: *"Pozdrav Lina, zovem se Denis, ja sam bagerista iz Cazina."*
* Verify Lina answers through speakers in natural Bosnian.
* Check that `Prijave (test)` in Airtable receives the new entry with phone, trade, and location.

### Step 3: Production Deployment with Docker Compose
```bash
cd "/Users/Agents/Lina JSI Gemini"
docker compose up -d --build
```
* Check container status: `docker compose ps`
* Monitor live logs: `docker compose logs -f`
* Stop container: `docker compose down`

---

## 7. Downstream HR Automations (Post-Call Setup)

After the call concludes and the candidate record is created in Airtable:

1. **Candidate Confirmation SMS:**
   - In Airtable: *Automations* ➔ *When record created in Prijave (test)* ➔ *Send SMS via Twilio*.
   - Message: *"Pozdrav {Ime}, tvoj termin za razgovor u Bihaću je {Casting termin}. Lokacija: Job-Step Bihać. Ponesi pasoš i diplomu!"*

2. **Document Collection via WhatsApp:**
   - Candidate is asked to send photos of their passport & diploma to the recruiting WhatsApp Business number.
   - Handled directly by recruiting staff or routed into Chatwoot.

3. **Recruiter Alert for High-Priority Profiles:**
   - Trigger: *When record matches condition* (`Status boravka = EU` OR `RADNO MJESTO contains Bagerista`).
   - Action: Send immediate Slack or Email notification to the lead recruiter.

---

## 8. Voice Branding & Replication

To replace the standard `Aoede` voice with a custom voice replica:
1. Record 2–5 minutes of clean audio from a native Bosnian speaker (24kHz WAV, no background noise).
2. Follow `VOICE_BRANDING_GUIDE.md` to create a voice profile in Google AI Studio via Gemini Flash TTS Voice Replication.
3. Once the voice ID is obtained, update `.env`:
   ```ini
   VOICE_NAME=voice_lina_jobstep_xxxx
   ```
4. Restart the server: `docker compose restart`.

---

## 9. Diagnostic & Troubleshooting Matrix

| Issue / Symptom | Root Cause | Exact Remedy |
| :--- | :--- | :--- |
| **`Airtable 403 Forbidden`** | Invalid token or missing scopes. | Check [airtable.com/create/tokens](https://airtable.com/create/tokens). Ensure scopes `data.records:read` AND `data.records:write` are selected. |
| **`Audio robotic or chipped`** | Sample rate mismatch. | Verify PBX audio codec. If FreeSWITCH sends 8000Hz, ensure `PBX_SAMPLE_RATE=8000` in `.env`. If using G.722, change to `16000`. |
| **`FreeSWITCH disconnects immediately`** | Server firewall blocking port 8000. | Run `sudo ufw allow 8000/tcp` on the server host and test connection with `wscat -c ws://<IPV4>:8000/ws/pbx`. |
| **`Gemini Quota / 1008 Error`** | API Key rate limit or billing block. | Test key in Google AI Studio. Check [console.cloud.google.com/billing](https://console.cloud.google.com/billing) if credit card verification is pending. |
| **`Candidate phone not saved`** | FreeSWITCH dialplan omitted `?caller_id=`. | Update dialplan URL to `ws://<IPV4>:8000/ws/pbx?caller_id=${caller_id_number}`. |
