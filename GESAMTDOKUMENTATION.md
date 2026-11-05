# 📖 Lina (Job-Step) - Die Gesamtdokumentation (End-to-End)

Das vollständige Handbuch für das KI-Recruiting-System **Lina** auf Basis von **Google Gemini 3.8 Live**, **FreeSWITCH PBX**, **Airtable** und nachgelagerten **HR-Automatisierungen**.

---

## 📑 Inhaltsverzeichnis
1. [Gesamtarchitektur](#1-gesamtarchitektur)
2. [Teil 1: Technische Einrichtung & Deployment](#teil-1-technische-einrichtung--deployment)
   - [Phase 1: API-Schlüssel vorbereiten](#phase-1-api-schlüssel-vorbereiten)
   - [Phase 2: Konfiguration (.env)](#phase-2-konfiguration-env)
   - [Phase 3: Server starten & deployen (Docker / Python)](#phase-3-server-starten--deployen)
   - [Phase 4: FreeSWITCH verbinden](#phase-4-freeswitch-verbinden)
   - [Phase 5: Erster Testanruf & Airtable-Prüfung](#phase-5-erster-testanruf--airtable-prüfung)
3. [Teil 2: Die 3 operativen HR-Folgeprozesse (Vor & nach dem Call)](#teil-2-die-3-operativen-hr-folgeprozesse)
   - [Baustein A: Automatische Bestätigung an den Bewerber (SMS / WhatsApp)](#baustein-a-automatische-bestätigung-an-den-bewerber)
   - [Baustein B: WhatsApp-Dokumentenkanal (Empfang von Pass & Diplom)](#baustein-b-whatsapp-dokumentenkanal)
   - [Baustein C: HR-Team Alerting bei A-Kandidaten](#baustein-c-hr-team-alerting-bei-a-kandidaten)
4. [Teil 3: Der vollständige Gesprächsleitfaden (System-Prompt)](#teil-3-der-vollständige-gesprächsleitfaden)
5. [Teil 4: Fehlerbehebung & FAQ](#teil-4-fehlerbehebung--faq)

---

## 1. Gesamtarchitektur

```
Anrufer (Kandidat aus Bosnien / Balkan)
       │
       ▼ (Telefonanruf via SIP/Festnetz)
[ FreeSWITCH PBX ]
       │
       ▼ (WebSocket Audio-Stream IPv4: ws://<IP>:8000/ws/pbx?caller_id=...)
[ Lina Voice Server (server.py) ]
       │
       ├── (16kHz / 24kHz Audio-Stream) ──▶ [ Google Gemini 3.8 Live ]
       │                                     (Lina: Bosnisch, menschliche Pausen)
       │
       ├── (Direktes Function Calling) ───▶ [ Airtable API ] (Tabelle: "Prijave (test)")
       │                                            │
       │                                            ▼
       │                                 [ Automatische Folgeprozesse ]
       │                                 ├─ SMS/WhatsApp an Bewerber (Baustein A)
       │                                 ├─ Foto-Empfang Pass/Diplom (Baustein B)
       │                                 └─ E-Mail/Slack Alert an Recruiter (Baustein C)
       │
       └── (Optional) ────────────────────▶ [ n8n Webhook / MCP Services ]
```

---

## Teil 1: Technische Einrichtung & Deployment

### Phase 0: Lokale KI-Assistenten & Skill-Integration

> **Lokale KI-Assistenten: Der Skill ist in Antigravity/Gemini, Claude Code und Codex global registriert.**

Das gesamte Wissen für Konfiguration, Dialplans, Airtable-Validierung, Tests und Deployment ist als modularer Skill hinterlegt:
* **Im Projekt:** [`skills/lina-voice-agent/SKILL.md`](skills/lina-voice-agent/SKILL.md)
* **Global für Google Antigravity & Gemini:** `~/.gemini/config/skills/lina-voice-agent/SKILL.md`
* **Global für Claude Code:** `~/.claude/skills/lina-voice-agent/SKILL.md` (via `~/.config/skillshare/skills/`)
* **Global für OpenAI Codex:** `~/.codex/skills/lina-voice-agent/SKILL.md`

Führen Sie auf einem neuen Rechner einfach `./setup_skills.sh` aus, um den Skill für alle Assistenten schlüsselfertig zu registrieren.

---

### Phase 1: API-Schlüssel vorbereiten
1. **Google Gemini API Key:**  
   Unter [aistudio.google.com](https://aistudio.google.com) ➔ Links auf **„Get API key“** ➔ **„Create API key“**.
2. **Airtable Personal Access Token & Base-ID:**  
   Unter [airtable.com/create/tokens](https://airtable.com/create/tokens) ➔ **„Create new token“**.  
   * **Name:** `Lina-Recruiting`  
   * **Scopes:** `data.records:read` und `data.records:write`  
   * **Base:** Ihre Recruiting-Base auswählen.  
   * Kopieren Sie das Token (`pat...`) und die Base-ID (`app...`, aus der Browser-URL der Tabelle).

---

### Phase 2: Konfiguration (.env)
1. Im Projektordner die Vorlage kopieren:
   ```bash
   cd "/Users/Agents/Lina JSI Gemini"
   cp .env.example .env
   ```
2. Die Datei `.env` mit Ihren Schlüsseln befüllen:
   ```ini
   # 1. Google Gemini API Key
   GEMINI_API_KEY=AIzaSy...DeinKeyHier

   # 2. Airtable Direktanbindung
   AIRTABLE_API_KEY=pat...DeinTokenHier
   AIRTABLE_BASE_ID=app...DeineBaseIDHier
   AIRTABLE_TABLE_NAME=Prijave (test)

   # 3. FreeSWITCH & Netzwerk (Reine IPv4)
   PBX_TYPE=freeswitch
   HOST=0.0.0.0
   PORT=8000
   PBX_SAMPLE_RATE=8000

   # 4. Stimme für Lina
   VOICE_NAME=Aoede
   ```

---

### Phase 3: Server starten & deployen

#### Option A: Mit Docker (Empfohlen für den 24/7 Betrieb)
```bash
docker compose up -d --build
```
* **Logs prüfen:** `docker compose logs -f`
* **Stoppen:** `docker compose down`

#### Option B: Direkt mit Python
```bash
pip install -r requirements.txt
python server.py
```

#### ✅ Health-Check im Browser prüfen:
Rufen Sie auf: `http://<DEINE-SERVER-IPV4>:8000/health`  
Antwort: `{"status":"healthy","agent":"Lina (Job-Step)","airtable_direct":true}` ➔ Alles betriebsbereit!

---

### Phase 4: FreeSWITCH verbinden
Fügen Sie an Ihrer Nebenstelle oder Inbound-Route in FreeSWITCH folgenden XML-Code ein:

```xml
<extension name="Lina_Recruiting_Agent">
  <condition field="destination_number" expression="^.*$">
    <action application="answer"/>
    <action application="playback" data="silence_stream://500"/>
    
    <!-- Audio-Stream direkt per IPv4 an Lina senden -->
    <action application="audio_stream" data="start ws://127.0.0.1:8000/ws/pbx?caller_id=${caller_id_number}"/>
  </condition>
</extension>
```
*(Wenn der Agent auf einem anderen Server läuft, ersetzen Sie `127.0.0.1` durch die IPv4 des Agenten-Servers).*

---

### Phase 5: Erster Testanruf & Airtable-Prüfung
1. Rufen Sie die Nebenstelle an.
2. Lina meldet sich auf Bosnisch:  
   *„Zdravo. Ja sam Lina, Job-Step... Zovem te kratko u vezi tvoje prijave za posao. Imaš li minut za par brzih pitanja?“*
3. Nennen Sie Schule (*„Mašinska škola Bihać“*) und Erfahrung (*„5 godina kao bravar“*).
4. Öffnen Sie Airtable: Alle Daten stehen sofort in der Tabelle **`Prijave (test)`**!

---

### Phase 6: Transkription, Anruf-Aufzeichnung & Langfuse-Tracing

#### 1. Worüber läuft die Transkription?
Die Transkription erfolgt **nativ und vollautomatisch direkt über Google Gemini 3.8 Live**:
* In `CONFIG` sind `input_audio_transcription` und `output_audio_transcription` aktiviert.
* Synchron zur Sprachverarbeitung sendet Gemini jedes gesprochene Wort des Anrufers in Echtzeit als Text (`server_content.input_transcription.text`).
* Linas eigene Antworten werden zeitgleich als Text (`server_content.output_transcription.text`) mitgeliefert.
* **Vorteil:** Sie benötigen **keinen Drittanbieter-Dienst** wie Whisper oder Deepgram für STT — das spart Kosten, Latenz und Server-Ressourcen.

#### 2. Worüber läuft die Anruf-Aufzeichnung (Call Recording)?
Sie haben die Wahl zwischen zwei sich perfekt ergänzenden Methoden:
* **Option 1: Server-seitige Aufzeichnung (`audio_recorder.py`):**
  * Bei jedem Anruf zeichnet der Server die rohen PCM-Frames des Anrufers und von Lina auf.
  * Beim Auflegen werden beide Spuren gemischt und als WAV-Datei abgelegt:  
    `recordings/call_<timestamp>_<caller_id>.wav`
  * Gleichzeitig wird ein vollständiges, sekundengenaues Text-Transkript gespeichert:  
    `recordings/call_<timestamp>_<caller_id>_transcript.txt`
  * Konfigurierbar über `.env`: `ENABLE_CALL_RECORDING=true`.
* **Option 2: PBX-seitige Telefonie-Aufzeichnung (FreeSWITCH):**
  * Fügen Sie im FreeSWITCH-Dialplan einfach folgende Zeile vor dem Audio-Stream ein:
    ```xml
    <action application="record_session" data="/var/lib/freeswitch/recordings/${uuid}.wav"/>
    ```
  * Damit speichert FreeSWITCH das gesamte Gespräch in bester Telefonie-Qualität direkt auf der PBX.

#### 3. Langfuse Observability & Tracing (`telemetry.py`)
Das System verfügt über einen integrierten Observability-Layer für [Langfuse](https://cloud.langfuse.com):
* **Trace-Erstellung:** Jeder Anruf erzeugt einen eigenen Trace mit Caller-ID, Model, Voice-Name und Tags (`bihac-casting`, `recruiting`).
* **Turns & Dialoge:** Alle gesprochenen Aussagen werden als strukturierte Events im Trace visualisiert.
* **Tool-Spans:** Jeder Schreibvorgang in Airtable (`sacuvaj_kandidata_u_airtable`) wird als eigener Span mit Eingabeparametern, Latenz und Antwort protokolliert.
* **Einrichtung:** Tragen Sie in `.env` einfach Ihre Keys ein:
  ```ini
  LANGFUSE_PUBLIC_KEY=pk-lf-...
  LANGFUSE_SECRET_KEY=sk-lf-...
  LANGFUSE_HOST=https://cloud.langfuse.com
  ```
  *(Fehlen die Keys, bleibt der Server voll funktionsfähig und läuft im lautlosen Fallback-Modus).*

---

## Teil 2: Die 3 operativen HR-Folgeprozesse

> **Wichtig:** Diese 3 Bausteine können ganz entspannt **NACH** dem Deployment eingerichtet werden. Der Agent (`server.py`) funktioniert völlig unabhängig davon!

---

### Baustein A: Automatische Bestätigung an den Bewerber
Sobald Lina auflegt, erhält der Bewerber eine schriftliche Bestätigung auf sein Smartphone.

#### Einrichtung in Airtable Automations (3 Minuten):
1. Öffnen Sie die Tabelle `Prijave (test)`.
2. Oben links: **„Automations“** ➔ **„Create automation“**.
3. **Trigger:** *„When a record is created“* in Table `Prijave (test)`.
4. **Action:** *„Send SMS (via Twilio)“* (oder *„Send email“*).
   * **To:** Feld `Telefon` aus dem Trigger wählen.
   * **Message:**
     ```text
     Zdravo! Hvala ti na razgovoru s Linom iz Job-Stepa. Tvoj termin za casting u Bihaću (16–20.11.) je zabilježen. 
     Molimo te da nam ovdje u poruci pošalješ sliku svoje diplome/svjedočanstva i pasoša. Radujemo se susretu!
     ```
5. Schalten Sie die Automation auf **„On“**.

---

### Baustein B: WhatsApp-Dokumentenkanal (Empfang von Pass & Diplom)
Lina bittet am Telefon um Fotos von Diplom, Pass und CV. Der Bewerber sendet diese Bilder direkt per WhatsApp an dieselbe Nummer.

* **Option 1 (Sofortstart in 5 Min):** Installieren Sie auf einem Firmenhandy die kostenlose App **WhatsApp Business** auf genau dieser Rufnummer. Eingehende Fotos poppen direkt auf dem Firmenhandy auf.
* **Option 2 (Agentur-Standard):** Verbinden Sie die WhatsApp Business API mit **Chatwoot** (wie in Ihrer ursprünglichen `agents.md` vorgesehen). Eingehende Dokumente landen in einem gemeinsamen Team-Postfach.

---

### Baustein C: HR-Team Alerting bei A-Kandidaten
Ihre Recruiter werden sofort alarmiert, wenn ein besonders wertvoller Bewerber (z. B. Baggerfahrer mit EU-Pass) qualifiziert wurde.

#### Einrichtung in Airtable Automations:
1. In Airtable: **„Automations“** ➔ **„Create automation“**.
2. **Name:** `Alarm: Top-Kandidat`.
3. **Trigger:** *„When a record matches conditions“*.
   * Bedingung: `Status boravka` **is** `EU` *ODER* `RADNO MJESTO` **contains** `bager`.
4. **Action:** *„Send email“* an `recruiting@job-step.com` (oder Slack / MS Teams):
   ```text
   🚨 Neuer Top-Bewerber qualifiziert!
   
   - Beruf: {KOMPANIJA} / {RADNO MJESTO}
   - Status Boravka: {Status boravka}
   - Telefon: {Telefon}
   - Notiz: {Bilješka}
   
   👉 Datensatz in Airtable öffnen: [Link]
   ```
5. Automation auf **„On“** schalten.

---

## Teil 3: Der vollständige Gesprächsleitfaden

Der Agent nutzt in [`prompts.py`](file:///Users/Agents/Lina%20JSI%20Gemini/prompts.py) folgende Kernlogik:

* **Strikter Dialekt:** Isključivo bosanski jezik (ijekavski), obraćanje na "ti", nema njemačkih/engleskih riječi.
* **Audio-Regie:** 15–20% sporiji govor, prirodne pauze od 1 sekunde, topao i blago nasmijan ton.
* **Begrüßung:** *„Zdravo. Ja sam Lina, Job-Step... Zovem te kratko u vezi tvoje prijave za posao. Imaš li minut za par brzih pitanja?“*
* **Kerneinwände:**
  * *4 Wochen Montage zu lang:* „Razumijem te... Ali velika prednost je što nakon toga imaš punu sedmicu kod kuće sa svojima, a smještaj i sav prevoz su ti potpuno plaćeni.“
  * *Lohn zu niedrig:* „Ovo je početna garantovana plata sa svim plaćenim dnevnicama i njemačkom prijavom, a prekovremeni sati se dodatno plaćaju.“
  * *Bist du ein Roboter?:* „Ja sam Lina, digitalna asistentica iz Job-Stepa... Tu sam da brzo zabilježim tvoje podatke kako bi naše kolege mogle odmah pripremiti tvoj profil za casting. Možemo li nastaviti?“
* **Zahlen & Fakten:** Turnus 4+1, Start 01.03.2027, Lohn 4.752–5.192 € (nur wenn er fragt), Casting Bihać 16.–20.11.

---

## Teil 4: Fehlerbehebung & FAQ

* **Frage: Muss n8n installiert sein?**  
  Nein. Die direkte Airtable-Anbindung läuft eigenständig in Python. n8n ist rein optional.
* **Frage: Kann ich die Stimme später austauschen?**  
  Ja. Tragen Sie in `.env` einfach den neuen Namen bei `VOICE_NAME` ein (z. B. Ihre eigene geklonte Voice-Design-ID) und starten Sie den Server neu.
* **Frage: Was tun bei abgehacktem Audio?**  
  Prüfen Sie `PBX_SAMPLE_RATE` in der `.env`. Standard-Telefonie nutzt `8000`, HD-Voice nutzt `16000`.
