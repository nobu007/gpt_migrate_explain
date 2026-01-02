#!/bin/bash
# BMAD TTS Hook - Simple echo version
# Usage: bmad-speak.sh '{agent-id}' '{response-text}'

AGENT_ID="$1"
RESPONSE_TEXT="$2"

echo "[BMAD TTS - $AGENT_ID]: $RESPONSE_TEXT"
