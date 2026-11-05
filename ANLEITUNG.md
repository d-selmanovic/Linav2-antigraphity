# 🚀 Schritt-für-Schritt-Anleitung: Lina Voice Agent (Job-Step)

Vollständige Anleitung zum Einrichten, Konfigurieren, Überwachen und produktiven Bereitstellen des KI-Telefonagenten **Lina** auf Basis von **Google Gemini 3.8 Live**, **FreeSWITCH (PBX)**, **Airtable**, **Langfuse** und **integriertem Error-Logging**.

---

## 📑 Inhaltsverzeichnis
1. [Übersicht & Architektur](#1-übersicht--architektur)
2. [Phase 1: Zugangsdaten vorbereiten](#phase-1-zugangsdaten-vorbereiten-2-minuten)
3. [Phase 2: Konfiguration (.env)](#phase-2-konfiguration-env-1-minute)
4. [Phase 3: Server starten, monitoren & deployen](#phase-3-server-starten-monitoren--deployen-2-minuten)
5. [Phase 4: FreeSWITCH (PBX) verbinden](#phase-4-freeswitch-pbx-verbinden-1-minute)
6. [Phase 5: Testanruf, Aufnahme & Airtable-Prüfung](#phase-5-testanruf-aufnahme--airtable-prüfung)
7. [Phase 6: Logging, Error-Tracking & Pre-Push Auditor](#phase-6-logging-error-tracking--pre-push-auditor)
8. [Fehlerbehebung (Troubleshooting)](#fehlerbehebung-troubleshooting)

---

## 1. Übersicht & Architektur

```
Anrufer (Bewerber)
       │
       ▼ (Ruft Nebenstelle an)
[ FreeSWITCH PBX ]
       │  (Optionale Aufnahme via record_session)
       ▼ (Audio-Stream via IPv4 WebSocket: ws://<IP>:8000/ws/pbx?caller_id=...)
[ Lina Voice Server (server.py) ]
       │
       ├── (16kHz / 24kHz Audio-Stream) ──▶ [ Google Gemini 3.8 Live ]
       │                                     (Lina: Bosnisch, menschliche Pausen)
       │
       ├── (Direktes Function Calling) ───▶ [ Airtable API ] (Tabelle: "Prijave (test)")
       │
       ├── (Anruf-Aufzeichnung & Text) ───▶ [ recordings/call_*.wav + *.txt ]
       │
       ├── (Observability & Tracing) ─────▶ [ Langfuse Tracing ] (telemetry.py)
       │
       ├── (Error-Logging & Metriken) ────▶ [ logs/lina.log & logs/error.log ]
       │
       └── (Optional) ────────────────────▶ [ n8n / MCP Services ]
```

---

## Phase 1: Zugangsdaten vorbereiten (2 Minuten)

Sie benötigen zwei API-Schlüssel:

### 1. Google Gemini API Key
* Öffnen Sie [aistudio.google.com](https://aistudio.google.com).
* Klicken Sie in der linken Leiste auf **„Get API key“**.
* Klicken Sie auf **„Create API key“** und kopieren Sie den Schlüssel (`AIzaSy...`).

### 2. Airtable Personal Access Token & Base-ID
* Öffnen Sie [airtable.com/create/tokens](https://airtable.com/create/tokens).
* Klicken Sie auf **„Create new token“**.
  * **Name:** `Lina-Recruiting`
  * **Scopes hinzufügen:** 
    * `data.records:read`
    * `data.records:write`
  * **Access:** Wählen Sie Ihre Recruiting-Base aus.
* Kopieren Sie das Token (`pat...`).
* **Base-ID finden:** Öffnen Sie Ihre Airtable-Tabelle im Browser. Die URL sieht so aus:  
  `https://airtable.com/appXXXXXXXXXXXXXX/tblYYYYYYYYYYYYYY/...`  
  Der Teil mit **`app...`** ist Ihre **Base-ID**.

---

## Phase 2: Konfiguration (.env) (1 Minute)

1. Navigieren Sie in den Projektordner:
   ```bash
   cd "/Users/Agents/Lina JSI Gemini"
   ```

2. Erstellen Sie die `.env`-Datei aus der Vorlage:
   ```bash
   cp .env.example .env
   ```

3. Öffnen Sie `.env` mit einem Texteditor und tragen Sie Ihre Daten ein:
   ```ini
   # 1. Google Gemini API Key
   GEMINI_API_KEY=AIzaSy...DeinGeminiKeyHier

   # 2. Airtable Direktanbindung
   AIRTABLE_API_KEY=pat...DeinAirtableTokenHier
   AIRTABLE_BASE_ID=app...DeineBaseIDHier
   AIRTABLE_TABLE_NAME=Prijave (test)

   # 3. FreeSWITCH & Netzwerk (Reine IPv4)
   PBX_TYPE=freeswitch
   HOST=0.0.0.0
   PORT=8000
   PBX_SAMPLE_RATE=8000

   # 4. Stimme für Lina (Aoede = warm und menschlich)
   VOICE_NAME=Aoede

   # 5. Anrufaufzeichnung (WAV & Text-Transkripte)
   ENABLE_CALL_RECORDING=true
   RECORDINGS_DIR=recordings

   # 6. Logging, Error-Tracking & Debugging
   LOGS_DIR=logs
   DEBUG_MODE=false

   # 7. Optional: Langfuse Tracing
   # LANGFUSE_PUBLIC_KEY=pk-lf-...
   # LANGFUSE_SECRET_KEY=sk-lf-...
   # LANGFUSE_HOST=https://cloud.langfuse.com

   # 8. Optional: n8n Webhook
   # N8N_WEBHOOK_URL=https://deine-n8n-instanz.com/webhook/lina
   ```

---

## Phase 3: Server starten, monitoren & deployen (2 Minuten)

Wählen Sie eine der beiden Start-Methoden:

### Option A: Mit Docker (Empfohlen für den Dauerbetrieb)
```bash
docker compose up -d --build
```
* **Status prüfen:** `docker compose ps`
* **Live-Logs ansehen:** `docker compose logs -f`
* **Stoppen:** `docker compose down`

### Option B: Direkt mit Python
```bash
pip install -r requirements.txt
python server.py
```

### ✅ Monitoring & Health-Endpoints
Öffnen Sie in Ihrem Web-Browser oder Terminal:
* **Gesundheits-Check:** `http://<SERVER-IPV4>:8000/health`
  ```json
  {
    "status": "healthy",
    "agent": "Lina (Job-Step)",
    "active_calls": 0,
    "total_calls": 12,
    "total_errors": 0
  }
  ```
* **Betriebsmetriken (Uptime, Anrufstatistik):** `http://<SERVER-IPV4>:8000/metrics`
* **Fehler-Log Puffer:** `http://<SERVER-IPV4>:8000/debug/errors`

---

## Phase 4: FreeSWITCH (PBX) verbinden (1 Minute)

Tragen Sie an Ihrer FreeSWITCH-Nebenstelle oder Inbound-Route die WebSocket-Verbindung mit der IPv4-Adresse ein:

```xml
<extension name="Lina_Recruiting_Agent">
  <condition field="destination_number" expression="^.*$">
    <!-- 1. Kanal annehmen -->
    <action application="answer"/>
    
    <!-- 2. Optionale Aufnahme auf PBX-Ebene -->
    <action application="record_session" data="/var/lib/freeswitch/recordings/${uuid}.wav"/>
    
    <!-- 3. Kurze Stille zur RTP-Pufferung -->
    <action application="playback" data="silence_stream://500"/>
    
    <!-- 4. Audio-Stream per IPv4 an Lina mit Caller-ID -->
    <action application="audio_stream" data="start ws://127.0.0.1:8000/ws/pbx?caller_id=${caller_id_number}"/>
  </condition>
</extension>
```

> **Hot-Reload der PBX ohne Neustart:**  
> Führen Sie in der FreeSWITCH-Konsole einfach aus:  
> `fs_cli -x "reloadxml"`

---

## Phase 5: Testanruf, Aufnahme & Airtable-Prüfung

1. Rufen Sie die Nebenstelle an.
2. **Gesprächsbeginn:** Lina meldet sich auf Bosnisch:
   > *„Zdravo. Ja sam Lina, Job-Step... Zovem te kratko u vezi tvoje prijave za posao. Imaš li minut za par brzih pitanja?“*
3. **Kandidaten-Antworten testen:**
   * Sagen Sie z. B.: *„Završio sam mašinsku školu u Bihaću, radio sam 5 godina kao bagerista i imam BiH pasoš.“*
4. **Ergebnisse prüfen:**
   * **In Airtable:** Tabelle `Prijave (test)` öffnen – alle Daten sind sofort eingetragen.
   * **Aufnahme:** Im Ordner `./recordings/` liegt die Datei `call_<timestamp>_<caller>.wav` und das vollständige Text-Transkript `*_transcript.txt`.
   * **In Langfuse:** Falls aktiviert, sehen Sie den vollständigen Trace mit Latenzen und Tool-Spans.

---

## Phase 6: Logging, Error-Tracking & Pre-Push Auditor

### 1. Rotierende Logs einsehen
* **Laufende Logs:** `tail -f logs/lina.log`
* **Fehler-Logbuch:** `cat logs/error.log`

### 2. Der Pre-Push Integrity Auditor
Verwenden Sie für zukünftige Updates immer das integrierte Prüf- und Deployment-Skript:
```bash
./commit_and_deploy.sh "feat: mein update"
```
Das Skript validiert Syntax, Abhängigkeiten, Umgebungsvariablen und Modul-Verdrahtung und pusht erst dann zu GitHub, wenn alles 100% konsistent ist.

---

## 🛠️ Fehlerbehebung (Troubleshooting)

| Problem | Ursache | Lösung |
| :--- | :--- | :--- |
| **Kein Ton / Verbindung bricht ab** | Falsche Audio-Abtastrate | Prüfen Sie in `.env` den Wert `PBX_SAMPLE_RATE=8000`. Falls FreeSWITCH auf HD-Voice (G.722) läuft, auf `16000` stellen. |
| **Airtable speichert nicht** | Token-Rechte fehlen | Prüfen Sie auf [airtable.com/create/tokens](https://airtable.com/create/tokens), ob `data.records:write` aktiviert ist. Siehe `logs/error.log`. |
| **Caller-ID ist leer** | FreeSWITCH übergibt Variable nicht | Stellen Sie sicher, dass in der URL `?caller_id=${caller_id_number}` mitgegeben wird. |
| **Fehler untersuchen** | Unbekannter Fehler aufgetreten | Öffnen Sie `http://localhost:8000/debug/errors` oder prüfen Sie `logs/error.log`. |
