# 📋 Lina (Job-Step) - Die operative HR-Prozess-Anleitung

Detaillierte Anleitung für die 3 Folge-Prozesse direkt nach dem Telefonat:
1. **Baustein A:** Automatische Bestätigung an den Bewerber (SMS / WhatsApp)
2. **Baustein B:** WhatsApp-Dokumentenkanal (Empfang von Pass & Diplom)
3. **Baustein C:** HR-Team-Alarmierung bei Top-Kandidaten (A-Kandidaten)

---

## ⏱️ Zeitplan & Einordnung

> **Wichtig:** Sie müssen diese 3 Punkte **nicht** vor dem Start des Agenten einrichten!  
> Der Agent (`server.py`) funktioniert eigenständig. Diese 3 Punkte reagieren auf Einträge in Airtable und können ganz entspannt **nach dem erfolgreichen Deployment** des Agenten dazugeschaltet werden.

---

## Baustein A: Automatische Bestätigung an den Bewerber (SMS / WhatsApp)

### Ziel:
Sobald Lina das Telefonat beendet und den Datensatz in Airtable anlegt, erhält der Bewerber innerhalb von 10 Sekunden eine schriftliche Nachricht auf sein Smartphone, damit er den Casting-Termin nicht vergisst und weiß, wohin er seine Unterlagen senden soll.

### Option 1: Einrichtung direkt in Airtable (Dauer: 3 Minuten, ohne Code)
1. Öffnen Sie Ihre Airtable-Tabelle **`Prijave (test)`**.
2. Klicken Sie oben links auf den Reiter **„Automations“** ➔ **„Create automation“**.
3. **Trigger konfigurieren:**
   * Wählen Sie: **„When a record is created“**.
   * Table: `Prijave (test)`.
4. **Action hinzufügen:**
   * Klicken Sie auf **„Add action“** ➔ Wählen Sie **„Send SMS (via Twilio)“** (oder **„Send email“**).
   * **To:** Klicken Sie auf das blaue `+` und wählen Sie das Feld `Telefon` aus dem Trigger.
   * **Message:** Fügen Sie diesen Text ein:
     ```text
     Zdravo! Hvala ti na razgovoru s Linom iz Job-Stepa. Tvoj termin za casting u Bihaću (16–20.11.) je zabilježen. 
     Molimo te da nam ovdje u poruci pošalješ sliku svoje diplome/svjedočanstva i pasoša. Radujemo se susretu!
     ```
5. Schalten Sie oben rechts den Schalter von **„Off“** auf **„On“**.

### Option 2: Einrichtung über n8n (Falls n8n im Einsatz ist)
* Unser Server schickt das Bewerberpaket an Ihren n8n-Webhook.
* In n8n erstellen Sie folgenden einfachen Node-Ablauf:
  ```
  [Webhook Node] ──▶ [WhatsApp Business Cloud API Node / Twilio SMS]
  ```
* Nachrichtentext: Dynamisch mit `{ $json.skola }`, `{ $json.casting_termin }`, etc.

---

## Baustein B: WhatsApp-Dokumentenkanal (Empfang von Pass & Diplom)

### Ziel:
Lina bittet am Telefon um Fotos von Diplom, Pass und CV. Der Bewerber sendet diese Bilder direkt per WhatsApp oder Viber an Ihre PBX-Rufnummer.

### Option 1: WhatsApp Business App auf Firmenhandy (Der schnellste Start)
1. Nehmen Sie ein Firmen-Smartphone.
2. Installieren Sie die offizielle, kostenlose App **WhatsApp Business** (iOS oder Android).
3. Registrieren Sie die App mit genau der Rufnummer, die Ihre PBX für Lina nutzt (die Verifizierung erfolgt per SMS oder Bestätigungsanruf).
4. Profil einrichten:
   * **Unternehmensname:** `Job-Step Recruiting`
   * **Kategorie:** Arbeitsvermittlung / Personalberatung
   * **Automatische Begrüßungsnachricht:**  
     *„Zdravo! Ovdje možete poslati slike diplome, pasoša i fotografiju za CV za casting u Bihaću. Naš tim će pregledati vaše dokumente.“*
5. **Ergebnis:** Sobald ein Bewerber nach dem Telefonat seine Zeugnisse fotografiert, landen sie direkt auf dem Firmenhandy.

### Option 2: Über Chatwoot (Zentrales Multi-User-Postfach – empfohlen für Teams)
1. Wenn mehrere Recruiter gleichzeitig eingehende Unterlagen bearbeiten:
2. Verbinden Sie die WhatsApp Business API mit **Chatwoot** (wie in Ihrer ursprünglichen `agents.md` vorgesehen).
3. Alle eingehenden Fotos landen in einer geteilten Inbox, können Bewerberakten zugewiesen und mit einem Klick in Airtable abgelegt werden.

---

## Baustein C: HR-Team-Alarmierung bei Top-Kandidaten (A-Kandidaten)

### Ziel:
Ihre Recruiter sollen sofort benachrichtigt werden, wenn ein besonders begehrter Bewerber (z. B. Baggerfahrer mit EU-Pass) qualifiziert wurde, um diesen Kandidaten bevorzugt zu behandeln.

### Einrichtung in Airtable Automations:
1. Gehen Sie in Airtable auf **„Automations“** ➔ **„Create automation“**.
2. **Name der Automation:** `Alarm: Top-Kandidat gefunden`.
3. **Trigger konfigurieren:**
   * Wählen Sie: **„When a record matches conditions“**.
   * Table: `Prijave (test)`.
   * **Bedingung (Condition):**  
     `Status boravka` **is** `EU`  
     *ODER*  
     `RADNO MJESTO` **contains** `bager` (oder z. B. `zidar`, `kran`).
4. **Action hinzufügen:**
   * Wählen Sie: **„Send email“** (an `recruiting@job-step.com`) oder **„Send Slack message“** / **„Send MS Teams message“**.
   * **Subject:** `🚨 Neuer Top-Bewerber qualifiziert: {Tačan naziv škole, grad, država}`
   * **Message:**
     ```text
     Lina hat soeben einen neuen A-Kandidaten am Telefon qualifiziert!
     
     - Beruf / Erfahrung: {KOMPANIJA} / {RADNO MJESTO}
     - Status Boravka: {Status boravka}
     - Telefonnummer: {Telefon}
     - Notiz aus dem Anruf: {Bilješka}
     
     👉 Jetzt Datensatz in Airtable aufrufen und nachfassen!
     ```
5. Schalten Sie die Automation auf **„On“**.

---

## 🏁 Zusammenfassung der Gesamtkette

```
1. Bewerber ruft an ➔ Lina führt Telefongespräch (Gemini 3.8 Live).
2. Auflegen ➔ Daten landen sekundenschnell in Airtable "Prijave (test)".
3. Automatische Bestätigung ➔ Bewerber erhält Bestätigung per SMS/WhatsApp (Baustein A).
4. Dokumenten-Upload ➔ Bewerber schickt Pass & Diplom per WhatsApp an Firmenhandy/Chatwoot (Baustein B).
5. Sofort-Alert ➔ Bei Top-Kandidaten klingelt sofort die E-Mail/Slack beim Recruiter (Baustein C).
```
