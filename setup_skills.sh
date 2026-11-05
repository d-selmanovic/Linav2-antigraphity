#!/usr/bin/env bash
# ==============================================================================
# setup_skills.sh — Installiert den Lina Voice Agent Skill für Antigravity, Claude & Codex
# ==============================================================================

set -e

SOURCE_SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills/lina-voice-agent"

if [ ! -d "$SOURCE_SKILL_DIR" ]; then
  echo "❌ Fehler: Quell-Skill-Verzeichnis nicht gefunden unter $SOURCE_SKILL_DIR"
  exit 1
fi

echo "🚀 Installiere Lina Voice Agent Skill für lokale KI-Assistenten..."

# 1. Google Antigravity & Gemini CLI
GEMINI_SKILLS_DIR="$HOME/.gemini/config/skills/lina-voice-agent"
mkdir -p "$GEMINI_SKILLS_DIR"
cp "$SOURCE_SKILL_DIR/SKILL.md" "$GEMINI_SKILLS_DIR/SKILL.md"
echo "  ✅ Google Antigravity & Gemini: $GEMINI_SKILLS_DIR/SKILL.md"

# 2. Claude Code (via ~/.config/skillshare/skills oder ~/.claude/skills)
if [ -d "$HOME/.config/skillshare/skills" ]; then
  CLAUDE_SKILLS_DIR="$HOME/.config/skillshare/skills/lina-voice-agent"
else
  CLAUDE_SKILLS_DIR="$HOME/.claude/skills/lina-voice-agent"
fi
mkdir -p "$CLAUDE_SKILLS_DIR"
cp "$SOURCE_SKILL_DIR/SKILL.md" "$CLAUDE_SKILLS_DIR/SKILL.md"
echo "  ✅ Claude Code:                 $CLAUDE_SKILLS_DIR/SKILL.md"

# 3. OpenAI Codex
CODEX_SKILLS_DIR="$HOME/.codex/skills/lina-voice-agent"
mkdir -p "$CODEX_SKILLS_DIR"
cp "$SOURCE_SKILL_DIR/SKILL.md" "$CODEX_SKILLS_DIR/SKILL.md"
echo "  ✅ OpenAI Codex:                $CODEX_SKILLS_DIR/SKILL.md"

echo ""
echo "🎉 Fertig! Der Lina Voice Agent Skill ist nun global für Antigravity, Claude Code und Codex aktiv."
echo "   Jeder Assistent erkennt das Projekt nun automatisch und kann Setup, Dialplan & Deployment steuern."
