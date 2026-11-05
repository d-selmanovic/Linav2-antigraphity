# AGENTS.md — Lina AI Voice Agent Repository Instructions

This document governs agent behavior (Antigravity, Gemini, OpenAI Codex, Claude Code, Cursor) when operating inside this repository.

---

## 1. Primary Skill & Documentation

For comprehensive operational guidance, troubleshooting, and deployment workflows, consult:
- **Project Skill:** `skills/lina-voice-agent/SKILL.md`
- **Global Skill Registration:** The skill is globally registered in:
  - Antigravity & Gemini: `~/.gemini/config/skills/lina-voice-agent/SKILL.md`
  - Claude Code: `~/.claude/skills/lina-voice-agent/SKILL.md`
  - OpenAI Codex: `~/.codex/skills/lina-voice-agent/SKILL.md`
  - Run `./setup_skills.sh` to reinstall or verify global registration on any host.
- **Master Documentation:** `GESAMTDOKUMENTATION.md`
- **Dialplan & Deployment Guide:** `ANLEITUNG.md`
- **Post-Call Automations:** `HR_OPERATIVER_PROZESS.md`
- **Voice Branding & TTS:** `VOICE_BRANDING_GUIDE.md`

---

## 2. Core Architecture & Rules

1. **AI Engine:**
   - Always target Google Gemini 3.8 Live (`models/gemini-3.8-live`) for real-time duplex calls.
   - For offline voice cloning / TTS, use `models/gemini-3.8-flash-tts`.

2. **Language & Persona Integrity:**
   - Lina speaks strictly **Bosnian (ijekavski)** with warm, professional, respectful informal addressing ("ti").
   - Pacing is audio-steered (-20% speed, deliberate 1-second pauses between thoughts, active listening acknowledgment "Razumijem...", "Odlično...").
   - Preserves objections handling for German field construction work (salary €4.752 – €5.192, Bihać casting 16–20.11.).

3. **Database Integration:**
   - Direct asynchronous Airtable client via `airtable_service.py`.
   - Never remove phone normalization logic (`+387` E.164).
   - Table name is `Prijave (test)`.

4. **PBX Telephony Stream:**
   - FreeSWITCH communicates over standard IPv4 WebSocket (`ws://<HOST>:8000/ws/pbx?caller_id=${caller_id_number}`).
   - Default sample rate is 8000 Hz (G.711 PCM). Resampling to/from 16kHz/24kHz is handled in `server.py`.

5. **Security & Secrets:**
   - Never log or commit raw API keys (`GEMINI_API_KEY`, `AIRTABLE_API_KEY`).
   - Keep `.env` strictly untracked in `.gitignore`.

---

## 3. Essential Commands

```bash
# Verify health without audio
curl http://localhost:8000/health

# Local interactive test with microphone
python test_local.py

# Production container deployment
docker compose up -d --build

# View real-time server logs
docker compose logs -f
```
