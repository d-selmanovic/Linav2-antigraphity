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
* `logger_config.py`: Strukturiertes Logging, rotierende Error-Logs & In-Memory Metriken.
* `commit_and_deploy.sh`: Vollautomatischer Pre-Push Integrity-Auditor, Skill-Synchronisierer & Deployer.
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

## 🤖 Framework-spezifische KI-Assistenten-Skills (Gemini, Claude & Codex)

> **Lokale KI-Assistenten: Für jedes Framework existiert eine maßgeschneiderte, tiefgehende Skill-Edition!**

Jeder KI-Coding-Assistent besitzt eigene Stärken, Tools und Befehlsstrukturen. Daher ist der Skill im Ordner `skills/` in drei dedizierten, hochpräzisen Editionen aufgebaut:

| Framework | Spezialisierung der Skill-Edition | Enthaltene Referenzen |
| :--- | :--- | :--- |
| **Google Antigravity & Gemini**<br>`~/.gemini/config/skills/lina-voice-agent/` | • Gemini 3.8 Live WebSocket-Protokoll (`LiveConnectConfig`)<br>• Bidirektionales Audio-Streaming & Resampling (8kHz ↔ 16kHz/24kHz)<br>• Native Live-Transkription (`input_` & `output_audio_transcription`)<br>• Bosnische Audio-Regie & Pacing („Govorna režija“ -20%)<br>• Gemini Flash TTS Voice Design & Replication | `references/gemini_live_protocol.md`<br>`references/audio_director_bosnian.md` |
| **Claude Code (Anthropic)**<br>`~/.claude/skills/lina-voice-agent/` | • Claude CLI Befehlsmuster & non-interaktive Ausführung<br>• FreeSWITCH XML Dialplan Integration & Hot-Reload (`fs_cli -x "reloadxml"`)<br>• Query-Parameter Forwarding (`caller_id=${caller_id_number}`)<br>• Downstream HR-Pipelines via n8n & WhatsApp Business / Chatwoot | `references/dialplan_freeswitch.md`<br>`references/operational_hr_automations.md` |
| **OpenAI Codex**<br>`~/.codex/skills/lina-voice-agent/` | • Deterministische Pydantic v2 Datenmodelle & Airtable-Schema<br>• Langfuse v2 Observability (Session-Traces, Tool-Spans, Latenzen)<br>• Defensive Fehlerbehandlung & Zero-Crash Fallbacks<br>• Multi-Stage Docker Container-Orchestrierung & Health-Checks | `references/schema_validation.md`<br>`references/langfuse_instrumentation.md`<br>`references/docker_production.md` |

### Automatisches 1-Klick Installationsskript (`setup_skills.sh`)
Wenn Sie dieses Projekt auf einem neuen Rechner klonen oder einen neuen Assistenten anbinden möchten, führen Sie einfach aus:
```bash
./setup_skills.sh
```
Das Skript kopiert und verlinkt jede maßgeschneiderte Edition automatisch in das jeweilige Konfigurationsverzeichnis von Antigravity, Claude Code und OpenAI Codex.

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

## 📊 Logging, Error-Tracking & Monitoring

### 1. Rotierendes Dateisystem-Logging (`logger_config.py`)
Das System trennt operative Logs und Fehlerberichte automatisch in zwei getrennte, rotierende Logdateien (max. 10 MB pro Datei, 5 automatische Backups):
* **`logs/lina.log`:** Vollständiger Ablauf aller Verbindungen, Transkripte und Tool-Aktivitäten.
* **`logs/error.log`:** Dedizierte Fehler- und Exception-Sammlung (nur `WARNING`, `ERROR` und `CRITICAL`) mit vollem Python-Stacktrace zur schnellen Ursachenanalyse.
* **Debug-Modus:** Setzen Sie `DEBUG_MODE=true` in der `.env`, um verboses Audio-Frame-Tracing zu aktivieren.

### 2. Live Monitoring & Health Endpoints
Der Server stellt HTTP-Schnittstellen für Status-Monitore (Prometheus, Zabbix, UptimeRobot, Datadog) bereit:
* **`GET /health`:** Schneller Status-Check (Online, Voice, Airtable-Status, aktive Anrufe).
* **`GET /metrics`:** Vollständige Telemetrie:
  ```json
  {
    "uptime_seconds": 3600.0,
    "uptime_human": "1h 0m 0s",
    "calls": { "total": 14, "active": 1, "successful": 13, "failed": 0 },
    "tool_calls": { "total": 13, "breakdown": { "sacuvaj_kandidata_u_airtable": 13 } },
    "health": { "error_count": 0, "last_error": null }
  }
  ```
* **`GET /debug/errors`:** Zeigt die letzten 20 aufgetretenen Fehler mit exakter Uhrzeit und Exception-Text.

---

## 🛡️ Pre-Push Auditor & Deployer (`commit_and_deploy.sh`)

Um sicherzustellen, dass niemals unvollständige Konfigurationen, vergessene Variablen oder unverdrahtete Module auf GitHub landen, steht das All-in-One-Skript `commit_and_deploy.sh` bereit:

```bash
# Ausführen vor jedem Git Push / Release:
./commit_and_deploy.sh "feat: mein neues feature"
```

### Was das Skript vollautomatisch prüft:
1. **Python-Syntax:** Kompiliert alle Python-Dateien (`py_compile`).
2. **Abhängigkeiten:** Gleicht alle `import`-Befehle im Code mit `requirements.txt` ab.
3. **Umgebungsvariablen:** Prüft, ob jedes `os.getenv()` in `.env.example` vollständig dokumentiert ist.
4. **Modul-Verdrahtung:** Verifiziert, ob alle Hilfsmodule (`audio_recorder`, `telemetry`, `logger_config`, `airtable_service`, `mcp_bridge`, `prompts`) fest in `server.py` eingebunden sind.
5. **Dokumentations-Integrität:** Prüft, ob alle in den READMEs verlinkten Dateien tatsächlich auf der Festplatte existieren.
6. **Skill-Synchronisation:** Führt `./setup_skills.sh` aus, um Antigravity, Claude Code und Codex auf den neuesten Stand zu bringen.
7. **Release-Packaging & Push:** Erstellt das bereinigte Download-ZIP in `~/Downloads/`, committed alle Änderungen und pusht sie zu GitHub.

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
