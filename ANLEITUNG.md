# 🚀 Schritt-für-Schritt-Anleitung: Lina Voice Agent (Job-Step)

Vollständige Anleitung zum Einrichten, Konfigurieren und produktiven Bereitstellen des KI-Telefonagenten **Lina** auf Basis von **Google Gemini 3.8 Live**, **FreeSWITCH (PBX)** und **Airtable**.

---

## 📑 Inhaltsverzeichnis
1. [Übersicht & Architektur](#1-übersicht--architektur)
2. [Phase 1: Zugangsdaten vorbereiten](#phase-1-zugangsdaten-vorbereiten-2-minuten)
3. [Phase 2: Konfiguration (.env)](#phase-2-konfiguration-env-1-minute)
4. [Phase 3: Server starten & deployen](#phase-3-server-starten--deployen-2-minuten)
5. [Phase 4: FreeSWITCH (PBX) verbinden](#phase-4-freeswitch-pbx-verbinden-1-minute)
6. [Phase 5: Testanruf & Airtable-Prüfung](#phase-5-testanruf--airtable-prüfung)
7. [Fehlerbehebung (Troubleshooting)](#fehlerbehebung-troubleshooting)

---

## 1. Übersicht & Architektur

```
Anrufer (Bewerber)
       │
       ▼ (Ruft Nebenstelle an)
[ FreeSWITCH PBX ]
       │
       ▼ (Audio-Stream via IPv4 WebSocket: ws://<IP>:8000/ws/pbx)
[ Lina Voice Server (server.py) ]
       │
       ├── (16kHz / 24kHz Audio-Stream) ──▶ [ Google Gemini 3.8 Live ]
       │                                     (Lina: Bosnisch, menschliche Pausen)
       │
       ├── (Direktes Function Calling) ───▶ [ Airtable API ] (Tabelle: "Prijave (test)")
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

1. Öffnen Sie das Terminal und navigieren Sie in den Projektordner:
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

   # 5. Optional: n8n Webhook
   # N8N_WEBHOOK_URL=https://deine-n8n-instanz.com/webhook/lina
   ```

---

## Phase 3: Server starten & deployen (2 Minuten)

Wählen Sie eine der beiden Start-Methoden:

### Option A: Mit Docker (Empfohlen für den Dauerbetrieb)
```bash
docker compose up -d --build
```
* **Status prüfen:** `docker compose ps`
* **Live-Logs ansehen:** `docker compose logs -f`

### Option B: Direkt mit Python
```bash
pip install -r requirements.txt
python server.py
```

### ✅ Funktionsprüfung (Health-Check)
Öffnen Sie in Ihrem Web-Browser:
```
http://<DEINE-SERVER-IPV4>:8000/health
```
Sie erhalten folgende Antwort:
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
*(Wenn `airtable_direct: true` steht, ist die Datenbankverbindung aktiv).*

---

## Phase 4: FreeSWITCH (PBX) verbinden (1 Minute)

Tragen Sie an Ihrer vorbereiteten FreeSWITCH-Nebenstelle oder Inbound-Route einfach die WebSocket-Verbindung mit der IPv4-Adresse ein:

```xml
<!-- In Ihrem FreeSWITCH Dialplan -->
<extension name="Lina_Recruiting_Agent">
  <condition field="destination_number" expression="^.*$">
    <action application="answer"/>
    <action application="playback" data="silence_stream://500"/>
    
    <!-- Audio-Stream direkt per IPv4 an Lina senden -->
    <action application="audio_stream" data="start ws://127.0.0.1:8000/ws/pbx?caller_id=${caller_id_number}"/>
  </condition>
</extension>
```

> **Hinweis zur IP-Adresse:**  
> * Wenn FreeSWITCH und der Voice-Agent auf **demselben Server** laufen: `127.0.0.1`  
> * Wenn FreeSWITCH auf einem **anderen Server** liegt: Ersetzen Sie `127.0.0.1` durch die **IPv4 des Agenten-Servers** (z. B. `192.168.1.50`).

---

## Phase 5: Testanruf & Airtable-Prüfung

1. Rufen Sie die Nebenstelle in FreeSWITCH an.
2. **Gesprächsbeginn:** Lina nimmt nach etwa einer halben Sekunde ab und begrüßt Sie auf Bosnisch:
   > *„Zdravo. Ja sam Lina, Job-Step... Zovem te kratko u vezi tvoje prijave za posao. Imaš li minut za par brzih pitanja?“*
3. **Kandidaten-Antworten testen:**
   * Sagen Sie z. B.: *„Završio sam mašinsku školu u Bihaću, radio sam 5 godina kao bravar u firmi Gradnja d.o.o. i živim u BiH.“*
4. **Ergebnis in Airtable prüfen:**
   * Öffnen Sie Ihre Airtable-Tabelle **`Prijave (test)`**.
   * Die Spalten `Tačan naziv škole, grad, država`, `KOMPANIJA`, `RADNO MJESTO`, `Status boravka` und `Telefon` sind sofort automatisch ausgefüllt!

---

## 🛠️ Fehlerbehebung (Troubleshooting)

| Problem | Ursache | Lösung |
| :--- | :--- | :--- |
| **Kein Ton / Verbindung bricht ab** | Falsche Audio-Abtastrate | Prüfen Sie in `.env` den Wert `PBX_SAMPLE_RATE=8000`. Falls FreeSWITCH auf HD-Voice (G.722) läuft, auf `16000` stellen. |
| **Airtable speichert nicht** | Token-Rechte fehlen | Prüfen Sie auf [airtable.com/create/tokens](https://airtable.com/create/tokens), ob `data.records:write` aktiviert ist. |
| **Caller-ID ist leer** | FreeSWITCH übergibt Variable nicht | Stellen Sie sicher, dass in der URL `?caller_id=${caller_id_number}` mitgegeben wird. |
