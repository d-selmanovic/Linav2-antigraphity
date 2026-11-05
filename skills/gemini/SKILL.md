---
name: lina-voice-agent
description: >
  Specialized Google Gemini & Antigravity operational skill for the Lina Voice Agent. Built specifically for
  Google Gemini 3.8 Live API, multimodal duplex audio streaming, native real-time transcription, audio resampling,
  and Gemini Voice Design/Replication.
license: Apache-2.0
metadata:
  framework: google-antigravity-gemini
  version: 2.2.0
  engine: gemini-3.8-live
  author: Step2Job / Job-Step
---

# Lina Voice Agent — Google Antigravity & Gemini Edition

This skill is engineered specifically for **Google Antigravity** and the **Google Gemini Live Ecosystem**. It provides granular architectural rules, multimodal audio protocol guidance, and Bosnian conversational steering for the Lina AI Voice Agent.

---

## 1. Gemini Multimodal Architecture & Audio Pipeline

Lina interfaces between standard narrowband telephony (FreeSWITCH PBX) and Google Gemini 3.8 Live:

```
[ FreeSWITCH PBX ] (8.000 Hz, 16-bit Mono PCM)
        │
        ▼ (WebSocket: /ws/pbx)
[ FastAPI server.py ]
        │
        ├──▶ Input Resampler (8kHz ➔ 16kHz) ──▶ session.send(audio=pcm_16k)
        │                                         │
        │                                         ▼
        │                               [ Google Gemini 3.8 Live ]
        │                               (models/gemini-3.8-live)
        │                                         │
        ├──◀ Output Resampler (24kHz ➔ 8kHz) ◀── model_turn (pcm_24k)
        │
        ├──▶ Native Real-Time Transcription (Input & Output)
        ├──▶ Dual-Track Audio Recording (audio_recorder.py)
        └──▶ Telemetry & Traces (telemetry.py ➔ Langfuse)
```

### Audio Resampling Specification
* **Telephony Input:** FreeSWITCH sends G.711 / Linear PCM at **8000 Hz** (160 samples per 20ms frame).
* **Gemini Input:** Gemini Live requires 16-bit Linear PCM at **16000 Hz** mono (`audio/pcm;rate=16000`).
* **Gemini Output:** Gemini Live streams synthesis at **24000 Hz** mono (`audio/pcm;rate=24000`).
* **Telephony Output:** `server.py` converts the 24kHz stream back to **8000 Hz** before writing to WebSocket.

---

## 2. Gemini Live Session Configuration (`LiveConnectConfig`)

Antigravity and Gemini agents must ensure `CONFIG` matches this exact specification in `server.py`:

```python
from google.genai import types

CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
        )
    ),
    # Native Speech-to-Text for caller and Lina simultaneously:
    input_audio_transcription=types.AudioTranscriptionConfig(),
    output_audio_transcription=types.AudioTranscriptionConfig(),
    # Context window management for long recruiting interviews:
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=104857,
        sliding_window=types.SlidingWindow(target_tokens=52428),
    ),
    system_instruction=types.Content(
        parts=[types.Part.from_text(text=LINA_SYSTEM_INSTRUCTION)],
        role="user",
    ),
    tools=[types.Tool(function_declarations=active_tools)]
)
```

---

## 3. Tool Calling Protocol with Gemini Live

Gemini Live executes tools via asynchronous server events:
1. `response.tool_call` contains `function_calls` list with unique `call_id` and dictionary `args`.
2. Lina executes the tool locally (`execute_tool_call` in `server.py` calling `airtable_service.py`).
3. The result is returned to the live session using `session.send_tool_response()`:
   ```python
   await session.send_tool_response(
       function_responses=[
           types.FunctionResponse(
               name=name,
               id=call_id,
               response={"result": tool_result}
           )
       ]
   )
   ```
4. Gemini immediately resumes speaking natural Bosnian to acknowledge the saved record.

---

## 4. Bosnian Linguistic & Audio-Director Pacing ("Govorna režija")

Gemini 3.8 models respond strongly to phonetic pacing directives embedded in the system prompt:

* **Tempo:** Always -15% to -20% slower than default English/German voice models.
* **Pauses:** Mandatory 1-second pause after welcoming and before asking questions.
* **Dialect:** Pure **Bosnian (ijekavski)**. Use informal "ti" with maximum warmth and professional respect.
* **Phonetic Counters:**
  * *Robot counter:* *"Ja sam Lina, digitalna asistentica iz Job-Stepa... Tu sam da brzo zabilježim tvoje podatke..."*
  * *Salary objection:* *"Razumijem te potpuno... Ovo je početna garantovana neto zarada sa svim plaćenim dnevnicama i smještajem..."*

---

## 5. Voice Design & Voice Replication via Gemini TTS

To migrate from the standard `Aoede` voice to a personalized branded Job-Step voice:
1. Record a 2–3 minute audio sample of a native Bosnian female speaker (24kHz WAV, mono).
2. Generate the voice replica ID using `models/gemini-3.8-flash-tts` Voice Replication API.
3. Configure in `.env`:
   ```ini
   VOICE_NAME=voice_lina_jobstep_production
   ```
4. Restart container: `docker compose restart`.

---

## 6. Antigravity Diagnostic Workflow

Whenever evaluating or auditing this system in Antigravity:
1. Read `.env` and verify `GEMINI_API_KEY`, `AIRTABLE_API_KEY`, and `AIRTABLE_BASE_ID`.
2. Inspect server health & metrics via:
   - `curl -s http://localhost:8000/health | jq .`
   - `curl -s http://localhost:8000/metrics | jq .`
   - `curl -s http://localhost:8000/debug/errors | jq .`
3. Verify that `input_audio_transcription` events are correctly populating `recordings/*_transcript.txt`.
4. Inspect `logs/lina.log` and `logs/error.log` for audio resampler or streaming exceptions.
5. Verify Langfuse traces under `telemetry.py`.
6. Run `./commit_and_deploy.sh` prior to finalizing any pull request or deployment.
