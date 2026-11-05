# FreeSWITCH Dialplan Integration & Audio Streaming Reference

## 1. Mod_audio_stream Requirements
FreeSWITCH requires `mod_audio_stream` or `mod_unimrcp` to stream raw audio over WebSockets:
```bash
# In fs_cli, verify module is loaded:
module_exists mod_audio_stream
```
If not loaded:
```bash
load mod_audio_stream
```

## 2. Audio Format & Codec Negotiation
* Narrowband: **PCMA** (G.711 A-law) or **PCMU** (G.711 u-law) at 8000 Hz.
* Wideband: **G.722** at 16000 Hz (update `PBX_SAMPLE_RATE=16000` in `.env`).

## 3. Query Parameter Forwarding
Always forward caller details in the query string:
`ws://<IP>:8000/ws/pbx?caller_id=${caller_id_number}&caller_name=${caller_id_name}`
The FastAPI server automatically parses this into `args["broj_telefona"]`.
