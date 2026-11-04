"""
Airtable Integration Service für Lina (Job-Step)
Ermöglicht das asynchrone Suchen, Anlegen und Aktualisieren von Bewerbern
direkt in Ihrer Airtable-Tabelle ("Prijave (test)").
"""

import os
import re
import logging
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger("AirtableService")

class AirtableService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_id: Optional[str] = None,
        table_name: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("AIRTABLE_API_KEY")
        self.base_id = base_id or os.getenv("AIRTABLE_BASE_ID")
        self.table_name = table_name or os.getenv("AIRTABLE_TABLE_NAME", "Prijave (test)")
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        
        if not self.api_key or not self.base_id:
            logger.warning("AirtableService: AIRTABLE_API_KEY oder AIRTABLE_BASE_ID fehlt in der Konfiguration!")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalisiert Telefonnummern für verlässliche Suche (z. B. +38761123456 oder 061123456)"""
        if not phone:
            return ""
        # Behalte nur Ziffern und führendes Plus
        cleaned = re.sub(r"[^\d+]", "", phone)
        # Wenn 00387..., ersetze mit +387
        if cleaned.startswith("00"):
            cleaned = "+" + cleaned[2:]
        return cleaned

    async def search_candidate_by_phone(self, phone: str) -> List[Dict[str, Any]]:
        """Sucht Kandidaten anhand der Telefonnummer in Airtable"""
        if not self.api_key or not self.base_id:
            logger.info(f"[SIMULATION] Suche nach Telefon: {phone}")
            return []

        clean_phone = self.normalize_phone(phone)
        # Suche flexibel nach Telefonnummer
        formula = f"SEARCH('{clean_phone}', {{Telefon}})"
        
        params = {"filterByFormula": formula, "maxRecords": 5}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.base_url, headers=self._headers(), params=params)
                if resp.status_code == 200:
                    records = resp.json().get("records", [])
                    logger.info(f"Airtable: {len(records)} Datensätze für {phone} gefunden.")
                    return records
                else:
                    logger.error(f"Airtable Fehler bei Suche ({resp.status_code}): {resp.text}")
                    return []
        except Exception as e:
            logger.error(f"Airtable Ausnahme bei Suche: {e}")
            return []

    async def save_or_update_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legt einen neuen Bewerber an oder aktualisiert einen bestehenden Eintrag in Airtable.
        Entspricht exakt den Vorgaben aus Ihrer agents.md / soul.md.
        """
        phone = candidate_data.get("broj_telefona", "")
        clean_phone = self.normalize_phone(phone)

        # Mappe Felder exakt auf Ihre Airtable-Spalten
        fields = {}
        if candidate_data.get("skola"):
            fields["Tačan naziv škole, grad, država"] = candidate_data["skola"]
        if candidate_data.get("radno_iskustvo"):
            fields["KOMPANIJA"] = candidate_data.get("firma", candidate_data["radno_iskustvo"])
            fields["RADNO MJESTO"] = candidate_data.get("radno_mjesto", "Radnik na terenu")
        if candidate_data.get("status_boravka"):
            fields["Status boravka"] = candidate_data["status_boravka"]
        if candidate_data.get("mjesto"):
            fields["Mjesto"] = candidate_data["mjesto"]
        if clean_phone:
            fields["Telefon"] = clean_phone
        if candidate_data.get("kratka_biljeska"):
            fields["Bilješka"] = candidate_data["kratka_biljeska"]
        if candidate_data.get("casting_termin"):
            fields["Casting termin"] = candidate_data["casting_termin"]

        if not self.api_key or not self.base_id:
            logger.info(f"[SIMULATION] Gespeichert in Airtable: {fields}")
            return {"status": "simulated", "fields": fields}

        # Prüfe zuerst, ob bereits ein Datensatz existiert
        existing = await self.search_candidate_by_phone(clean_phone) if clean_phone else []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if existing:
                    # Update bestehenden Datensatz
                    record_id = existing[0]["id"]
                    url = f"{self.base_url}/{record_id}"
                    logger.info(f"Airtable: Aktualisiere Record {record_id}...")
                    resp = await client.patch(url, headers=self._headers(), json={"fields": fields})
                else:
                    # Neuen Datensatz anlegen
                    logger.info("Airtable: Lege neuen Bewerber-Datensatz an...")
                    resp = await client.post(self.base_url, headers=self._headers(), json={"fields": fields})

                if resp.status_code in [200, 201]:
                    logger.info("Airtable: Erfolgreich gespeichert!")
                    return {"status": "success", "record": resp.json()}
                else:
                    logger.error(f"Airtable Fehler beim Speichern ({resp.status_code}): {resp.text}")
                    return {"status": "error", "message": resp.text}
        except Exception as e:
            logger.error(f"Airtable Ausnahme beim Speichern: {e}")
            return {"status": "error", "message": str(e)}
