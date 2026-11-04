# 🎙️ Lina (Job-Step) - Audio-Branding & Stimm-Anleitung

Anleitung für das perfekte Audio-Branding: Weg von der Standardstimme hin zu einer exklusiven, maßgeschneiderten Unternehmensstimme für Job-Step, die zu 100 % nach einer echten bosnischen Recruiterin klingt.

---

## 🎯 Das Ziel

Bewerber sollen nicht das Gefühl haben, mit einem Computer oder Assistenten zu sprechen.  
Der Eindruck am Telefon soll sein: **„Ich habe gerade mit Lina aus dem Job-Step Büro telefoniert.“**

---

## 🛠️ Wo richtet man das ein?

In **Google AI Studio** unter dem Bereich:  
👉 [aistudio.google.com/generate-speech](https://aistudio.google.com/generate-speech) (Modell: `Gemini 3.8 Flash TTS`).

Sie haben zwei Wege zur Auswahl:

---

## Weg A: „Voice Design“ (Prompt-basiert – In 2 Minuten fertig, 0 Aufnahmen)

Sie müssen niemanden aufnehmen. Sie beschreiben Google die Stimme per Text:

### Schritt-für-Schritt:
1. Öffnen Sie in Google AI Studio den Bereich **„Explore thousands of voices“**.
2. Klicken Sie auf **`+ Create new voice`**.
3. Geben Sie folgende genaue Beschreibung für Linas Stimme ein:
   ```text
   A warm, authentic 28-year-old female HR recruiter from Sarajevo, Bosnia.
   Vocal timbre: Warm, articulate, polite, melodic chest voice with natural vocal fry at the end of sentences.
   Pacing: Relaxed, unhurried, natural conversational cadence with subtle breathing sounds.
   Style: Professional yet very empathetic and friendly, speaking authentic Bosnian ijekavski.
   ```
4. Klicken Sie auf **„Generate sample“** und hören Sie sich die Sprachprobe an.
5. Speichern Sie die Stimme unter dem Namen `Lina-JobStep`.
6. **Ergebnis:** Google generiert eine eindeutige Kennung, z. B. `voice_lina_jobstep_98234`.

---

## Weg B: „Voice Replication“ (Voice Cloning – Echte Kollegin klonen)

Das absolute Premium-Ergebnis: Eine echte Mitarbeiterin aus Ihrem Team oder eine bosnische Sprecherin wird geklont.

### Schritt-für-Schritt:
1. **Aufnahme erstellen (2 bis 3 Minuten):**
   * Setzen Sie die Kollegin in einen ruhigen Raum mit einem guten Headset oder USB-Mikrofon.
   * Lassen Sie sie 15 typische Recruiting-Sätze einsprechen:
     * *„Zdravo, ja sam Lina iz Job-Stepa. Zovem te povodom tvoje prijave za posao u Njemačkoj.“*
     * *„Casting se održava u Bihaću od šesnaestog do dvadesetog novembra.“*
     * *„Plata je od četiri hiljade sedamsto pedeset do pet hiljada sto devedeset eura bruto sa uključenim dnevnicama.“*
     * *„Koju školu imaš završenu i gdje si do sada radio?“*
     * *„Rad na terenu traje četiri sedmice, a nakon toga imaš jednu slobodnu sedmicu.“*
   * Speichern Sie die Audiodatei als WAV oder MP3.
2. **In Google AI Studio hochladen:**
   * Gehen Sie auf **„Voice replication“**.
   * Laden Sie die Datei hoch.
   * Google lernt in ca. 60 Sekunden die Stimmfarbe und Melodie der Kollegin.
3. Speichern Sie die Stimme und notieren Sie sich die erzeugte `voice_id`.

---

## ⚡ Wie binde ich die neue Stimme in den Agenten ein?

Sie müssen im Python-Code **nichts programmieren**. Sie tauschen lediglich in der Datei `.env` eine Zeile aus:

```ini
# VORHER:
VOICE_NAME=Aoede

# NACHHER (Ihre neue ID einfügen):
VOICE_NAME=voice_lina_jobstep_98234
```

Starten Sie den Server neu:
```bash
python server.py
# bzw. bei Docker:
docker compose restart
```

Ab sofort meldet sich Lina bei jedem Anruf über FreeSWITCH mit Ihrer exklusiven Firmenstimme!
