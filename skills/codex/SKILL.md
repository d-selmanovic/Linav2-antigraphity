---
name: lina-voice-agent
description: >
  Specialized OpenAI Codex operational skill for the Lina Voice Agent. Built specifically for OpenAI Codex,
  deterministic code execution, Pydantic schema validation, Langfuse v2 tracing, and Docker container orchestration.
license: Apache-2.0
metadata:
  framework: openai-codex
  version: 2.2.0
  engine: codex-execution-engine
  author: Step2Job / Job-Step
---

# Lina Voice Agent — OpenAI Codex Edition

This skill provides deterministic code execution routines, strict schema mappings, Langfuse telemetry specifications, and production deployment patterns for **OpenAI Codex** when maintaining or extending the Lina Voice Agent.

---

## 1. Codex Execution Directives

When writing code or generating scripts for this repository:
1. **Target Python 3.10+ / 3.11:** Use standard `typing`, `asyncio`, and modern Pydantic v2 structures.
2. **Defensive Programming:** Always provide fallback defaults when reading environment variables (`os.getenv(...)`).
3. **No Unhandled Exceptions in WebSocket Loops:** The audio streaming loop in `server.py` must catch `WebSocketDisconnect` and `asyncio.CancelledError` cleanly without raising unhandled 500 errors.
4. **Deterministic Testing:** Run `python test_local.py` or execute automated curls against `/health`.

---

## 2. Deterministic Schema Definitions

### Airtable Payload Schema for `Prijave (test)`
Codex must enforce these exact field mappings inside `airtable_service.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional

class CandidateApplication(BaseModel):
    skola: str = Field(..., alias="Tačan naziv škole, grad, država")
    kompanija: str = Field(default="Step2Job / Job-Step", alias="KOMPANIJA")
    radno_mjesto: str = Field(..., alias="RADNO MJESTO")
    status_boravka: str = Field(default="BiH", alias="Status boravka")
    mjesto: str = Field(..., alias="Mjesto")
    telefon: str = Field(..., alias="Telefon")
    casting_termin: str = Field(default="16.-20.11. Bihać", alias="Casting termin")
    biljeska: Optional[str] = Field(default="", alias="Bilješka")
```

### Phone Normalization Regex
* Input: `061 123 456` or `061-123-456` ➔ Output: `+38761123456`
* Input: `+387 61 123 456` ➔ Output: `+38761123456`

---

## 3. Langfuse v2 Telemetry & Tracing Patterns

Codex must use the unified `LinaTracer` in `telemetry.py` to instrument call lifecycles:

```python
from telemetry import LinaTracer

tracer = LinaTracer()

# 1. Start Trace
trace = tracer.start_call_trace(
    call_id=call_id,
    caller_id=caller_id,
    metadata={"model": "models/gemini-3.8-live", "sample_rate": 8000}
)

# 2. Track Tool Execution (Span)
tool_span = trace.span(name="tool:sacuvaj_kandidata_u_airtable", input=args)
try:
    result = await airtable_service.save_or_update_candidate(args)
    tool_span.end(output=result, level="DEFAULT")
except Exception as e:
    tool_span.end(output=str(e), level="ERROR", status_message=str(e))

# 3. Finalize Trace & Flush
trace.update(output={"status": "completed", "recording": wav_path})
tracer.flush()
```

---

## 4. Production Docker & Health Verification

### Deployment Commands:
```bash
# Build and run containers detached:
docker compose up -d --build

# Verify container health:
curl -f -s http://localhost:8000/health | jq .

# Tail application logs:
docker compose logs -f --tail=50
```

### Expected Healthcheck JSON:
```json
{
  "status": "healthy",
  "agent": "Lina (Job-Step)",
  "model": "models/gemini-3.8-live",
  "voice": "Aoede",
  "airtable_direct": true,
  "n8n_connected": false,
  "mcp_enabled": true,
  "call_recording_enabled": true,
  "langfuse_tracing_enabled": true,
  "active_calls": 0,
  "total_calls": 24,
  "total_errors": 0
}
```

---

## 5. Codex Troubleshooting Commands

```bash
# Check if port 8000 is open and listening
netstat -an | grep 8000

# Inspect local WAV call recordings and error logs
ls -lh recordings/
tail -n 50 logs/error.log

# Fetch Prometheus / JSON live operational metrics
curl -s http://localhost:8000/metrics | jq .

# Verify Python syntax across all core modules
python3 -m py_compile server.py airtable_service.py audio_recorder.py telemetry.py logger_config.py prompts.py

# Run the 7-step pre-push integrity auditor & deployer
./commit_and_deploy.sh "chore: codex automated audit"
```
