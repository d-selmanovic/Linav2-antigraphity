# CLAUDE.md — Claude Code Guidelines for Lina Voice Agent

## Project Overview
Real-time duplex Voice AI Agent for recruiting construction workers (Bihać casting 16-20.11., Step2Job / Job-Step). Built with Google Gemini 3.8 Live API, FastAPI, FreeSWITCH PBX audio stream (IPv4 WebSocket), direct Airtable database integration, and Model Context Protocol (MCP).

## Relevant Files & Skills
- **Claude Skill Edition:** `skills/claude/SKILL.md` (references in `skills/claude/references/`, installed in `~/.claude/skills/lina-voice-agent/`)
- **Other Editions:** `skills/gemini/SKILL.md` (Gemini), `skills/codex/SKILL.md` (Codex), `skills/lina-voice-agent/SKILL.md` (Universal)
- **Installer:** Run `./setup_skills.sh` to install or sync across all local assistants.
- **Core Server:** `server.py` (FastAPI + WebSocket + 8kHz ↔ 16/24kHz audio resampler, native transcription, barge-in)
- **Call Recorder:** `audio_recorder.py` (Dual-channel audio mix to `.wav`, timestamped transcript export to `.txt`)
- **Telemetry:** `telemetry.py` (Langfuse session & tool tracing with zero-crash dummy fallback)
- **Database Client:** `airtable_service.py` (`Prijave (test)` table upsert)
- **Prompt & Persona:** `prompts.py` (Bosnian ijekavski prompt & tool declarations)
- **Extensibility:** `mcp_bridge.py` (Model Context Protocol bridge)
- **Local Test Suite:** `test_local.py` (Terminal microphone/speaker test)
- **Container Setup:** `Dockerfile`, `docker-compose.yml`

## Environment Configuration
Ensure `.env` contains:
- `GEMINI_API_KEY`: Google AI Studio API key (`AIzaSy...`)
- `AIRTABLE_API_KEY`: Airtable Personal Access Token (`pat...`)
- `AIRTABLE_BASE_ID`: Airtable Base ID (`app...`)
- `AIRTABLE_TABLE_NAME`: Default `Prijave (test)`
- `HOST`: `0.0.0.0`
- `PORT`: `8000`
- `PBX_SAMPLE_RATE`: `8000`
- `VOICE_NAME`: `Aoede`
- `ENABLE_CALL_RECORDING`: `true`
- `LANGFUSE_PUBLIC_KEY`: Optional (`pk-lf-...`)
- `LANGFUSE_SECRET_KEY`: Optional (`sk-lf-...`)
- `LANGFUSE_HOST`: Optional (`https://cloud.langfuse.com`)

## Verification Commands
- Health check: `curl http://localhost:8000/health`
- Interactive local test: `python test_local.py`
- Run container: `docker compose up -d --build`
- Logs: `docker compose logs -f`
