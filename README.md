# 🎙️ Lina (Job-Step) - AI Voice Agent Server

Produktionsreifer Sprachagent auf Basis von **Google Gemini 3.8 Live** mit **direkter Airtable-Anbindung**, **PBX-Telefonschnittstelle (WebSockets)**, **MCP-Kompatibilität** und optionalem **n8n-Gateway**.

---

## 📑 Inhaltsverzeichnis
1. [Architektur](#-architektur)
2. [Dateien im Projekt](#-dateien-im-projekt)
3. [Voraussetzungen & Vorbereitung](#-voraussetzungen--vorbereitung)
4. [Lokale Einrichtung](#-lokale-einrichtung)
5. [Airtable Konfiguration](#-airtable-konfiguration)
6. [PBX / Telefonanlagen-Anbindung](#-pbx--telefonanlagen-anbindung)
7. [MCP-Erweiterung (Model Context Protocol)](#-mcp-erweiterung)
8. [Deployment-Anleitung (Produktion)](#-deployment-anleitung)
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
* `requirements.txt`: Python-Abhängigkeiten.
* `.env.example`: Vorlage für alle Umgebungsvariablen.

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
