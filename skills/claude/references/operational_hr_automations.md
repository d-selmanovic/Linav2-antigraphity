# Downstream HR Automations & WhatsApp Intake Reference

## 1. Candidate Confirmation SMS via Airtable Automations
* **Trigger:** Record created in table `Prijave (test)`
* **Condition:** Field `Telefon` is not empty
* **Action:** Twilio / MessageBird SMS
* **Template:**
  > *"Pozdrav {Ime}, tvoj termin za razgovor u Bihaću je {Casting termin}. Lokacija: Job-Step Bihać. Ponesi pasoš i diplomu sa sobom!"*

## 2. Document Collection via WhatsApp Business
* Candidates reply to the confirmation SMS/WhatsApp with smartphone photos of:
  1. Passport (BiH or EU)
  2. School graduation certificate / Diploma
* Documents are received in Chatwoot or the WhatsApp Business Inbox and linked to the Airtable candidate ID.

## 3. High-Priority Recruiter Alerts
* **Slack / Teams Notification:** Triggered if `Status boravka` is 'EU' or `RADNO MJESTO` contains 'bagerista/kranista'.
* Alert goes immediately to lead recruiting coordinator for direct outreach.
