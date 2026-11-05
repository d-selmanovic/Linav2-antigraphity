# 🎙️ Lina (Job-Step) - AI Voice Agent Server

Produktionsreifer Sprachagent auf Basis von **Google Gemini 3.8 Live** mit **direkter Airtable-Anbindung**, **PBX-Telefonschnittstelle (WebSockets)**, **MCP-Kompatibilität** und optionalem **n8n-Gateway**.

---

## 📑 Inhaltsverzeichnis
1. [Architektur](#-architektur)
2. [Dateien im Projekt](#-dateien-im-projekt)
3. [Lokale KI-Assistenten (Skill-Integration)](#-lokale-ki-assistenten-skill-integration)
4. [Voraussetzungen & Vorbereitung](#-voraussetzungen--vorbereitung)
5. [Lokale Einrichtung](#-lokale-einrichtung)
6. [Airtable Konfiguration](#-airtable-konfiguration)
7. [PBX / Telefonanlagen-Anbindung](#-pbx--telefonanlagen-anbindung)
8. [Transkription, Aufnahme & Langfuse-Tracing](#-transkription-aufnahme--langfuse-tracing)
9. [MCP-Erweiterung (Model Context Protocol)](#-mcp-erweiterung)
10. [Deployment-Anleitung (Produktion)](#-deployment-anleitung)
   - [A. Mit Docker & Docker-Compose (Empfohlen)](#a-mit-docker--docker-compose)
   - [B. Als Linux Systemd Service](#b-als-linux-systemd-service)
   - [C. Cloud Deployment (Railway / Google Cloud Run)](#c-cloud-deployment)

---

## 🏗️ Architektur

```
Anrufer (Kandidat aus BiH/Balkan)
       │
       ▼ (Telefonanruf via SIP/Festnetz)
[ Eigene PBX (Asterisk / FreePBX / 3CX) ]
       │
       ▼ (WebSocket Audio-Stream 8kHz G.711 / PCM)
[ FastAPI Server (server.py) ]
       │
       ├── (16kHz/24kHz Audio-Stream) ──▶ [ Google Gemini 3.8 Live ]
       │                                  (Lina: Bosnisch, warm, Pausen, Einwandbehandlung)
       │
       ├── (Direktes Function Calling) ─▶ [ Airtable API ] (Tabelle: "Prijave (test)")
       │
       ├── (MCP Tool Routing) ──────────▶ [ Beliebige MCP-Server ] (Kalender, CRM)
       │
       └── (Optionaler Webhook) ────────▶ [ n8n Workflow ] (WhatsApp / SMS / Alerts)
```

---

## 📂 Dateien im Projekt

* `server.py`: Hauptserver (FastAPI) mit PBX-WebSockets, Gemini-Live-Bridge und Tool-Dispatcher.
* `airtable_service.py`: Direkte asynchrone Schnittstelle zur Airtable-API (Suchen, Anlegen, Aktualisieren).
* `mcp_bridge.py`: Schnittstelle zum Model Context Protocol (für spätere Zusatz-Tools).
* `prompts.py`: Linas optimierter bosnischer System-Prompt (Audio-Regie, Pausen, Einwandbehandlung).
* `test_local.py`: Lokales Testskript über Mac-/PC-Mikrofon und Lautsprecher.
* `Dockerfile` & `docker-compose.yml`: Für schlüsselfertiges 1-Klick-Deployment.
* `audio_recorder.py`: Anrufaufzeichnung (WAV-Mix) und Transkriptions-Export (.txt).
* `telemetry.py`: Langfuse LLM-Observability & Tracing-Integration.
* `requirements.txt`: Python-Abhängigkeiten.
* `.env.example`: Vorlage für alle Umgebungsvariablen.
* `skills/lina-voice-agent/SKILL.md`: Autonomer Skill für alle gängigen KI-Coding-Assistenten.
* `setup_skills.sh`: 1-Klick Installationsskript zur globalen Registrierung des Skills.
* `AGENTS.md`: Universelle Steuerungsdatei für OpenAI Codex, Antigravity und Cursor.
* `CLAUDE.md`: Spezifikationsdatei für Claude Code.
* `GESAMTDOKUMENTATION.md`: Umfassendes End-to-End Handbuch (Technik, PBX, HR-Prozess).
* `ANLEITUNG.md`: FreeSWITCH Dialplan & Server-Setup Anleitung.
* `HR_OPERATIVER_PROZESS.md`: Post-Call Workflows (SMS, WhatsApp-Dokumentenempfang, Recruiter-Alerts).
* `VOICE_BRANDING_GUIDE.md`: Anleitung für Gemini 3.8 Flash TTS Voice Design & Replication.

---

## 🤖 Lokale KI-Assistenten (Skill-Integration)

> **Lokale KI-Assistenten: Der Skill ist in Antigravity/Gemini, Claude Code und Codex global registriert.**

Jeder Entwickler oder Administrator kann dieses Repository mit jedem modernen KI-Coding-Assistenten öffnen. Der Skill [`skills/lina-voice-agent/SKILL.md`](skills/lina-voice-agent/SKILL.md) ist auf dem Host-System global in allen drei Assistenten-Ecosystemen registriert:

| KI-Assistent | Globaler Registrierungspfad | Erkennungsmechanismus |
| :--- | :--- | :--- |
| **Google Antigravity & Gemini** | `~/.gemini/config/skills/lina-voice-agent/SKILL.md` | Antigravity Customization Engine / Native Skills |
| **Claude Code** | `~/.claude/skills/lina-voice-agent/SKILL.md` | Claude Skill Directory (`~/.config/skillshare/skills/`) & `CLAUDE.md` |
| **OpenAI Codex** | `~/.codex/skills/lina-voice-agent/SKILL.md` | Codex Global Skills & `AGENTS.md` |

### Automatisches 1-Klick Installationsskript (`setup_skills.sh`)
Wenn Sie dieses Projekt auf einem neuen Rechner klonen oder einen neuen Assistenten anbinden möchten, führen Sie einfach aus:
```bash
./setup_skills.sh
```
Das Skript kopiert und verlinkt den Skill automatisch in alle vorhandenen Konfigurationsverzeichnisse von Antigravity, Claude Code und OpenAI Codex.

Sobald der Skill registriert ist, versteht jeder KI-Assistent automatisch:
1. Wie `.env` konfiguriert und validiert wird.
2. Wie das Airtable-Schema `Prijave (test)` aufgebaut sein muss.
3. Wie der FreeSWITCH-Dialplan konfiguriert wird (inkl. `caller_id=${caller_id_number}`).
4. Wie Tests (`test_local.py`, `/health`) und Docker-Deployments durchgeführt werden.

---

## ⚙️ Voraussetzungen & Vorbereitung

1. **Google Gemini API Key:** Erhältlich unter [aistudio.google.com](https://aistudio.google.com).
2. **Airtable Personal Access Token:** Erhältlich unter [airtable.com/create/tokens](https://airtable.com/create/tokens).
   * Benötigte Scopes: `data.records:read`, `data.records:write`, `schema.bases:read`.
3. **Python 3.10+** oder **Docker**.

---

## 💻 Lokale Einrichtung

1. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Umgebungsvariablen einrichten:**
   ```bash
   cp .env.example .env
   ```
   Tragen Sie Ihre Keys in `.env` ein:
   ```ini
   GEMINI_API_KEY=AIzaSy...
   AIRTABLE_API_KEY=pat...
   AIRTABLE_BASE_ID=app...
   AIRTABLE_TABLE_NAME=Prijave (test)
   VOICE_NAME=Aoede
   ```

3. **Lokalen Mikrofon-Test starten:**
   ```bash
   python test_local.py
   ```
   Sagen Sie *„Dobar dan!“* ins Mikrofon. Lina antwortet auf Bosnisch und schreibt die genannten Daten live in Ihre Airtable-Tabelle.

---

## 🗄️ Airtable Konfiguration

Das Skript befüllt exakt folgende Spalten in Ihrer Tabelle `Prijave (test)`:
* `Tačan naziv škole, grad, država` (Single line text)
* `KOMPANIJA` (Single line text)
* `RADNO MJESTO` (Single line text)
* `Status boravka` (Single line text oder Single select: BiH / EU)
* `Mjesto` (Single line text)
* `Telefon` (Phone / Text - wird automatisch normalisiert)
* `Casting termin` (Single line text)
* `Bilješka` (Long text)

---

## 📞 PBX / Telefonanlagen-Anbindung

Die Telefonanlage verbindet sich per WebSocket mit dem Server:
* **WebSocket URL:** `ws://<DEINE-SERVER-IP>:8000/ws/pbx`
* **Audio-Format:** 16-Bit Linear PCM, Standard 8.000 Hz Mono (oder G.711 PCMA/PCMU).
* Der Server rechnet die Abtastrate automatisch zwischen Ihrer PBX (8 kHz) und Gemini Live (16 kHz Input / 24 kHz Output) um.

---

## 🎙️ Transkription, Aufnahme & Langfuse-Tracing

### 1. Transkription (Wie funktioniert die Spracherkennung?)
Lina nutzt die **native bidirektionale Streaming-Transkription** von Google Gemini 3.8 Live (`input_audio_transcription` und `output_audio_transcription`):
* **Anrufer:** Die gesprochenen Worte des Anrufers werden synchron im Event-Stream (`server_content.input_transcription.text`) bereitgestellt. Es wird **kein separater STT-Dienst** (wie Whisper oder Deepgram) benötigt — keine zusätzliche Latenz, keine extra API-Kosten.
* **Lina:** Jedes von Lina gesprochene Wort wird parallel als Text übertragen (`server_content.output_transcription.text`).
* **Barge-in / Unterbrechung:** Wenn der Anrufer Lina unterbricht, erkennt Gemini dies sofort (`server_content.interrupted`) und der Server leert augenblicklich den Audio-Puffer zur Telefonanlage.

### 2. Anrufaufzeichnung (Call Recording)
Sie haben zwei parallele Möglichkeiten für die Aufzeichnung:
1. **Server-seitig (`audio_recorder.py`):**
   * Zeichnet Caller-Audio und Agent-Audio auf und mischt sie in eine standardisierte WAV-Datei.
   * Ablageort: `./recordings/call_<timestamp>_<caller_id>.wav`
   * Exportiert zeitgleich ein chronologisches Text-Transkript mit Sekunden-Zeitstempeln: `./recordings/call_<timestamp>_<caller_id>_transcript.txt`.
   * Steuerbar über `.env`: `ENABLE_CALL_RECORDING=true` und `RECORDINGS_DIR=recordings`.
2. **PBX-seitig (FreeSWITCH Dialplan):**
   * Im FreeSWITCH-Dialplan vor dem WebSocket-Start einfach eintragen:
     ```xml
     <action application="record_session" data="/var/lib/freeswitch/recordings/${uuid}.wav"/>
     ```

### 3. Langfuse Observability & Tracing (`telemetry.py`)
Das System verfügt über eine integrierte Anbindung an **Langfuse**:
* **Session-Tracing:** Jeder Anruf wird als Trace mit Session-ID, Caller-ID, Modell und Tags angelegt.
* **Turns & Events:** Jede Sprachäußerung von Anrufer und Lina wird protokolliert.
* **Tool-Spans:** Jeder Aufruf der Airtable-Datenbank oder des n8n-Webhooks wird mit Parametern, Ausführungsdauer (Latenz) und Erfolgsstatus (`success` / `error`) aufgezeichnet.
* **Ausfallsicherer Dummy-Modus:** Sind keine Langfuse-Keys konfiguriert, arbeitet das Tracing geräuschlos im Hintergrund ohne Leistungsverlust oder Abstürze.

---

## 🔌 MCP-Erweiterung

Wenn Sie zukünftig beliebige MCP-Server anbinden möchten:
1. Erstellen Sie eine Datei `mcp_servers.json`:
   ```json
   {
     "mcpServers": {
       "calendar": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-google-calendar"]
       }
     }
   }
   ```
2. Die `mcp_bridge.py` lädt die Werkzeuge automatisch und übergibt sie an Gemini Live.

---

## 🚀 Deployment-Anleitung

### A. Mit Docker & Docker-Compose (Empfohlen)

1. Stellen Sie sicher, dass Ihre `.env`-Datei ausgefüllt ist.
2. Starten Sie den Container im Hintergrund:
   ```bash
   docker compose up -d --build
   ```
3. Der Server ist sofort online unter Port `8000`. Logs prüfen mit:
   ```bash
   docker compose logs -f
   ```

---

### B. Als Linux Systemd Service (Auf Ubuntu/Debian Server)

1. Kopieren Sie den Projektordner z. B. nach `/opt/lina-voice-agent`.
2. Erstellen Sie die Service-Datei `/etc/systemd/system/lina.service`:
   ```ini
   [Unit]
   Description=Lina AI Voice Agent
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/opt/lina-voice-agent
   ExecStart=/usr/local/bin/uvicorn server:app --host 0.0.0.0 --port 8000
   Restart=always
   EnvironmentFile=/opt/lina-voice-agent/.env

   [Install]
   WantedBy=multi-user.target
   ```
3. Service aktivieren und starten:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable lina
   sudo systemctl start lina
   ```

---

### C. Cloud Deployment (Railway / Google Cloud Run)

* **Railway:** Verbinden Sie einfach das GitHub-Repository. Railway erkennt das `Dockerfile` automatisch und fragt Sie nach den Umgebungsvariablen (`GEMINI_API_KEY`, etc.).
* **Google Cloud Run:**
  ```bash
  gcloud run deploy lina-voice-agent \
    --source . \
    --platform managed \
    --region europe-west1 \
    --allow-unauthenticated
  ```
