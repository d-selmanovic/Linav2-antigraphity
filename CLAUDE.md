# CLAUDE.md — Claude Code Guidelines for Lina Voice Agent

## Project Overview
Real-time duplex Voice AI Agent for recruiting construction workers (Bihać casting 16-20.11., Step2Job / Job-Step). Built with Google Gemini 3.8 Live API, FastAPI, FreeSWITCH PBX audio stream (IPv4 WebSocket), direct Airtable database integration, and Model Context Protocol (MCP).

## Relevant Files & Skills
- **Skill Definition:** `skills/lina-voice-agent/SKILL.md` (globally registered in `~/.claude/skills/lina-voice-agent/`, `~/.gemini/config/skills/lina-voice-agent/`, and `~/.codex/skills/lina-voice-agent/`. Reinstall via `./setup_skills.sh`.)
- **Core Server:** `server.py` (FastAPI + WebSocket + 8kHz ↔ 16/24kHz audio resampler)
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

## Verification Commands
- Health check: `curl http://localhost:8000/health`
- Interactive local test: `python test_local.py`
- Run container: `docker compose up -d --build`
- Logs: `docker compose logs -f`
