#!/usr/bin/env bash
# ==============================================================================
# setup_skills.sh — Installiert maßgeschneiderte Skills für Gemini, Claude & Codex
# ==============================================================================

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$BASE_DIR/skills"

echo "🚀 Installiere framework-spezifische Lina Voice Agent Skills..."

# 1. Google Antigravity & Gemini CLI (Spezifisch für Gemini 3.8 Live & Multimodal Audio)
GEMINI_TARGET="$HOME/.gemini/config/skills/lina-voice-agent"
mkdir -p "$GEMINI_TARGET/references"
cp "$SKILLS_DIR/gemini/SKILL.md" "$GEMINI_TARGET/SKILL.md"
cp -r "$SKILLS_DIR/gemini/references/"* "$GEMINI_TARGET/references/" 2>/dev/null || true
echo "  ✅ Google Antigravity & Gemini: $GEMINI_TARGET (Gemini Live & Audio Pacing)"

# 2. Claude Code (Spezifisch für Claude CLI, FreeSWITCH Dialplans & HR-Workflows)
if [ -d "$HOME/.config/skillshare/skills" ]; then
  CLAUDE_TARGET="$HOME/.config/skillshare/skills/lina-voice-agent"
else
  CLAUDE_TARGET="$HOME/.claude/skills/lina-voice-agent"
fi
mkdir -p "$CLAUDE_TARGET/references"
cp "$SKILLS_DIR/claude/SKILL.md" "$CLAUDE_TARGET/SKILL.md"
cp -r "$SKILLS_DIR/claude/references/"* "$CLAUDE_TARGET/references/" 2>/dev/null || true
echo "  ✅ Claude Code:                 $CLAUDE_TARGET (CLI Dialplans & HR Pipelines)"

# 3. OpenAI Codex (Spezifisch für deterministische Schemas, Langfuse & Docker)
CODEX_TARGET="$HOME/.codex/skills/lina-voice-agent"
mkdir -p "$CODEX_TARGET/references"
cp "$SKILLS_DIR/codex/SKILL.md" "$CODEX_TARGET/SKILL.md"
cp -r "$SKILLS_DIR/codex/references/"* "$CODEX_TARGET/references/" 2>/dev/null || true
echo "  ✅ OpenAI Codex:                $CODEX_TARGET (Schemas, Langfuse & Docker)"

echo ""
echo "🎉 Fertig! Jeder Assistent hat nun seine spezialisierte Skill-Edition erhalten:"
echo "   • Gemini/Antigravity ➔ Multimodal Audio Streaming, 8kHz/16kHz/24kHz Resampling, Bosnian Audio-Director"
echo "   • Claude Code        ➔ FreeSWITCH Dialplans, XML Hot-Reload, n8n/Chatwoot HR Pipelines"
echo "   • OpenAI Codex       ➔ Pydantic Schemas, Langfuse v2 Spans, Docker Production Orchestration"
