#!/usr/bin/env bash
# ==============================================================================
# commit_and_deploy.sh — Automatisierter Pre-Push Auditor, Deployer & Skill-Sync
# ==============================================================================

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}==============================================================================${RESET}"
echo -e "${BOLD}${BLUE} 🎙️  Lina Voice Agent — Pre-Commit, Integrity Audit & Deployment Tool ${RESET}"
echo -e "${BOLD}${BLUE}==============================================================================${RESET}"
echo ""

AUDIT_FAILED=0

# ------------------------------------------------------------------------------
# 1. Python Syntax & Kompilierungsprüfung
# ------------------------------------------------------------------------------
echo -e "${BOLD}[1/7] Prüfe Python-Syntax und Kompilierung...${RESET}"
for py_file in $(find . -maxdepth 1 -name "*.py"); do
  if python3 -m py_compile "$py_file" 2>/dev/null; then
    echo -e "  ${GREEN}✓${RESET} $py_file kompiliert fehlerfrei"
  else
    echo -e "  ${RED}✗ FEHLER in $py_file${RESET}"
    AUDIT_FAILED=1
  fi
done

# ------------------------------------------------------------------------------
# 2. Abhängigkeiten-Audit (requirements.txt vs. imports)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}[2/7] Prüfe Abhängigkeiten (requirements.txt)...${RESET}"
KNOWN_STDLIB="os sys time json uuid asyncio logging typing wave math re subprocess shutil"
REQ_CONTENT=$(cat requirements.txt | tr '[:upper:]' '[:lower:]')

# Bekannte Modul-Mappings
# google-genai -> google.genai
# python-dotenv -> dotenv
# pyairtable -> pyairtable
# fastapi -> fastapi
# uvicorn -> uvicorn
# httpx -> httpx
# numpy -> numpy
# langfuse -> langfuse
# mcp -> mcp
# pydantic -> pydantic

for py_file in $(find . -maxdepth 1 -name "*.py"); do
  IMPORTS=$(grep -E '^\s*(import|from)\s+[a-zA-Z0-9_]+' "$py_file" | awk '{print $2}' | cut -d'.' -f1 | sort -u)
  for imp in $IMPORTS; do
    # Ignoriere Standard-Bibliothek und lokale Projektdateien
    if echo "$KNOWN_STDLIB" | grep -qw "$imp"; then continue; fi
    if [ -f "./$imp.py" ]; then continue; fi
    
    # Check ob Modul in requirements.txt erwähnt wird
    CHECK_NAME="$imp"
    if [ "$imp" == "dotenv" ]; then CHECK_NAME="dotenv"; fi
    if [ "$imp" == "genai" ] || [ "$imp" == "google" ]; then CHECK_NAME="google-genai"; fi

    if echo "$REQ_CONTENT" | grep -qi "$CHECK_NAME"; then
      : # Alles ok
    else
      echo -e "  ${YELLOW}⚠ Warnung:${RESET} Modul '$imp' in $py_file könnte in requirements.txt fehlen!"
    fi
  done
done
echo -e "  ${GREEN}✓${RESET} Abhängigkeiten-Audit abgeschlossen"

# ------------------------------------------------------------------------------
# 3. Umgebungsvariablen-Audit (.env.example vs. os.getenv)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}[3/7] Prüfe Umgebungsvariablen (.env.example vs Code)...${RESET}"
CODE_VARS=$(grep -rEo 'os\.getenv\("[A-Z0-9_]+"' *.py 2>/dev/null | cut -d'"' -f2 | sort -u)
EXAMPLE_CONTENT=$(cat .env.example)

MISSING_VARS=0
for var in $CODE_VARS; do
  if echo "$EXAMPLE_CONTENT" | grep -q "$var="; then
    echo -e "  ${GREEN}✓${RESET} $var ist in .env.example dokumentiert"
  else
    echo -e "  ${RED}✗ FEHLEND:${RESET} $var wird im Code genutzt, fehlt aber in .env.example!"
    MISSING_VARS=$((MISSING_VARS + 1))
    AUDIT_FAILED=1
  fi
done

# ------------------------------------------------------------------------------
# 4. Verdrahtungs-Prüfung (Sind alle Erweiterungen eingebunden?)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}[4/7] Prüfe Verdrahtung der Module in server.py...${RESET}"
CORE_MODULES="airtable_service audio_recorder telemetry logger_config mcp_bridge prompts"
for mod in $CORE_MODULES; do
  if grep -q "$mod" server.py; then
    echo -e "  ${GREEN}✓${RESET} $mod.py ist fest in server.py verdrahtet"
  else
    echo -e "  ${RED}✗ UNVERDRAHTET:${RESET} $mod.py wird in server.py nicht importiert!"
    AUDIT_FAILED=1
  fi
done

# ------------------------------------------------------------------------------
# 5. Dokumentations- und Dateilink-Integrität
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}[5/7] Prüfe Existenz aller dokumentierten Kern-Dateien...${RESET}"
DOC_FILES=(
  "README.md"
  "GESAMTDOKUMENTATION.md"
  "ANLEITUNG.md"
  "HR_OPERATIVER_PROZESS.md"
  "VOICE_BRANDING_GUIDE.md"
  "AGENTS.md"
  "CLAUDE.md"
  "setup_skills.sh"
  "skills/gemini/SKILL.md"
  "skills/claude/SKILL.md"
  "skills/codex/SKILL.md"
  "skills/lina-voice-agent/SKILL.md"
  "docker-compose.yml"
  "Dockerfile"
)

for file in "${DOC_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo -e "  ${GREEN}✓${RESET} $file existiert"
  else
    echo -e "  ${RED}✗ FEHLT:${RESET} Dokumentation verweist auf $file, Datei existiert nicht!"
    AUDIT_FAILED=1
  fi
done

# Abbruch bei schwerwiegenden Audit-Fehlern
if [ "$AUDIT_FAILED" -eq 1 ]; then
  echo ""
  echo -e "${RED}${BOLD}❌ Audit fehlgeschlagen! Bitte Fehler vor dem Commit beheben.${RESET}"
  exit 1
fi

# ------------------------------------------------------------------------------
# 6. Skill-Synchronisation für Antigravity, Claude & Codex
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}[6/7] Synchronisiere Skills für lokale KI-Assistenten...${RESET}"
./setup_skills.sh

# Aktualisiere Scratch-Spiegel falls vorhanden
SCRATCH_DIR="/Users/activi/.gemini/antigravity/scratch/lina-voice-agent"
if [ -d "$SCRATCH_DIR" ]; then
  cp -r skills setup_skills.sh *.py *.md docker-compose.yml .gitignore .env.example "$SCRATCH_DIR/" 2>/dev/null || true
  echo -e "  ${GREEN}✓${RESET} Scratch-Spiegel synchronisiert"
fi

# ------------------------------------------------------------------------------
# 7. Download-ZIP neu schnüren, Committen & Pushen
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}[7/7] Erstelle sauberes ZIP-Bundle & Git Commit / Push...${RESET}"

DOWNLOAD_ZIP="/Users/activi/Downloads/Lina-Voice-Agent-V2.zip"
rm -f "$DOWNLOAD_ZIP" Lina-Voice-Agent-V2.zip
zip -r "$DOWNLOAD_ZIP" . -x "*.git*" "*.DS_Store" "*__pycache__*" "*.zip" ".env" "recordings/*" "logs/*" >/dev/null
cp "$DOWNLOAD_ZIP" "./Lina-Voice-Agent-V2.zip"
echo -e "  ${GREEN}✓${RESET} ZIP-Bundle aktualisiert: $DOWNLOAD_ZIP"

# Git Status prüfen
git add -A
if git diff --cached --quiet; then
  echo -e "  ${BLUE}ℹ Keine ungespeicherten Git-Änderungen vorhanden.${RESET}"
else
  COMMIT_MSG="${1:-chore: automated pre-push audit, skill sync and deployment update}"
  git commit -m "$COMMIT_MSG"
  echo -e "  ${GREEN}✓${RESET} Neuer Commit erstellt: $COMMIT_MSG"
fi

# Push zu GitHub
echo "  🚀 Pushe Änderungen zu origin main..."
git push origin main
echo -e "  ${GREEN}✓${RESET} Erfolgreich auf GitHub aktualisiert: https://github.com/d-selmanovic/Linav2-antigraphity"

# ------------------------------------------------------------------------------
# Live-Health-Check (falls Server läuft)
# ------------------------------------------------------------------------------
echo ""
if curl -s -f -m 2 http://localhost:8000/health >/dev/null 2>&1; then
  echo -e "${BOLD}📡 Live Server Status (http://localhost:8000):${RESET}"
  curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || true
else
  echo -e "${YELLOW}ℹ Lokaler Server läuft aktuell nicht auf Port 8000 (Start mit: docker compose up -d)${RESET}"
fi

echo ""
echo -e "${BOLD}${GREEN}==============================================================================${RESET}"
echo -e "${BOLD}${GREEN} 🎉 ALLES BEREIT & GEPRÜFT! Deployment & Skills sind 100% synchron. ${RESET}"
echo -e "${BOLD}${GREEN}==============================================================================${RESET}"
