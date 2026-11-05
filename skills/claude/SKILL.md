---
name: lina-voice-agent
description: >
  Specialized Claude Code operational skill for the Lina Voice Agent. Built specifically for Claude Code CLI,
  FreeSWITCH PBX dialplans, FastAPI server administration, n8n webhook routing, and downstream HR automations.
license: Apache-2.0
metadata:
  framework: anthropic-claude-code
  version: 2.2.0
  engine: claude-code-cli
  author: Step2Job / Job-Step
---

# Lina Voice Agent — Claude Code Edition

This skill provides specialized execution patterns, command references, and dialplan automation routines for **Claude Code** when configuring, deploying, or debugging the Lina Voice Agent.

---

## 1. Claude Code CLI Operational Conventions

When executing tasks in this codebase as Claude Code:
1. **Never guess paths:** The canonical repository root is `/Users/Agents/Lina JSI Gemini`.
2. **Execute non-interactive commands:** Always run commands with explicit timeouts and structured output.
3. **Verify before completing:** Always query `curl -s http://localhost:8000/health` and verify Docker status before concluding any deployment turn.
4. **Secrets protection:** Never print or commit contents of `.env` or files inside `recordings/`.

---

## 2. Fast Command Cheat Sheet for Claude Code

| Operation | Command |
| :--- | :--- |
| **Check Server Health** | `curl -s http://localhost:8000/health \| jq .` |
| **Inspect Telemetry & Metrics** | `curl -s http://localhost:8000/metrics \| jq .` |
| **Inspect Error Logs** | `tail -n 50 logs/error.log` |
| **Run Pre-Push Audit & Deploy** | `./commit_and_deploy.sh "commit message"` |
| **Inspect Active Calls** | `docker compose logs --tail=100 -f` |
| **Test Mic Locally** | `python test_local.py` |
| **Reload FreeSWITCH Dialplan** | `fs_cli -x "reloadxml"` |
| **Check Port Binding** | `lsof -i :8000` |
| **Verify Recordings Folder** | `ls -lh recordings/` |
| **Audit Git State** | `git status -s` |

---

## 3. FreeSWITCH XML Dialplan Setup & Hot-Reloading

Claude Code can inspect and configure `/etc/freeswitch/dialplan/default/` on the PBX server:

```xml
<extension name="Lina_Recruiting_Agent">
  <condition field="destination_number" expression="^.*$">
    <!-- 1. Answer call -->
    <action application="answer"/>
    
    <!-- 2. PBX-side Call Recording (Optional) -->
    <action application="record_session" data="/var/lib/freeswitch/recordings/${uuid}.wav"/>
    
    <!-- 3. Stabilize RTP stream -->
    <action application="playback" data="silence_stream://500"/>
    
    <!-- 4. WebSocket stream with caller_id parameter -->
    <action application="audio_stream" data="start ws://<SERVER_IPV4>:8000/ws/pbx?caller_id=${caller_id_number}"/>
  </condition>
</extension>
```

> **Hot-Reload:** After editing the dialplan, tell the user or run:  
> `fs_cli -x "reloadxml"`

---

## 4. Downstream HR Automations (Claude Pipeline Reference)

Post-call workflows run asynchronously once `sacuvaj_kandidata_u_airtable` commits:

```
[ server.py ] ──▶ Airtable: "Prijave (test)"
       │
       ├──▶ [ Airtable Automation ] ──▶ Twilio SMS: Terminbestätigung Bihać (16–20.11.)
       │
       ├──▶ [ n8n Webhook ] ─────────▶ Chatwoot / WhatsApp Business (Pass & Diplom Upload)
       │
       └──▶ [ Lead Scoring ] ────────▶ Slack Alert (#recruiting-lead-alerts)
```

### Recruiter Filter Rules:
* **High Priority (Sofort-Interview):** `Status boravka == "EU"` AND `RADNO MJESTO` contains `Bagerista|Kranista|Zidar`.
* **Standard Priority:** `Status boravka == "BiH"` (Visum-Prozess über Step2Job).

---

## 5. Claude Code Troubleshooting Playbook

### Issue: `PBX connects but disconnects after 1 second`
1. Check if FreeSWITCH receives a 404 or connection refused:
   `curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://<SERVER_IPV4>:8000/ws/pbx`
2. Ensure firewall allows TCP port 8000:
   `sudo ufw allow 8000/tcp`

### Issue: `Airtable record not created`
1. Check token in `.env`: `grep AIRTABLE_API_KEY .env` (must start with `pat...`).
2. Verify token permissions at [airtable.com/create/tokens](https://airtable.com/create/tokens) for scopes `data.records:write` and base access.
3. Check `docker compose logs | grep -i airtable`.
