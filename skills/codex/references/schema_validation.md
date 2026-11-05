# Schema Validation & Error Recovery Reference

## 1. Schema Mapping Table
```python
AIRTABLE_COLUMN_MAP = {
    "skola": "Tačan naziv škole, grad, država",
    "kompanija": "KOMPANIJA",
    "radno_mjesto": "RADNO MJESTO",
    "status_boravka": "Status boravka",
    "mjesto": "Mjesto",
    "broj_telefona": "Telefon",
    "casting_termin": "Casting termin",
    "iskustvo_i_napomena": "Bilješka",
}
```

## 2. Error Recovery Rules
* Missing `broj_telefona`: Fall back to URL query parameter `caller_id` from FreeSWITCH PBX.
* Invalid phone format: Strip non-digits except leading `+`. If begins with `0`, replace with `+387`.
* Empty trade/position: Set default `"Građevinski radnik (Opšti profil)"`.
